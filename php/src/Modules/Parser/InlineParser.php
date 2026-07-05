<?php

declare(strict_types=1);

namespace MintWiki\Parser;

use MintWiki\Ui\Escaper;

/**
 * NamuMark풍 인라인 문법을 HTML 조각으로 변환하는 파서 (태스크 0704).
 *
 * 블록 요소(제목/목록/표/문단 분리, 0705)와 최종 렌더 조립(0706)은 이
 * 클래스의 책임이 아니다 — 이 클래스는 한 텍스트 조각 안의 인라인 마크업만
 * 처리한다.
 *
 * 지원 문법:
 * - `'''굵게'''` -> `<strong>`
 * - `''기울임''` -> `<em>`
 * - `__밑줄__` -> `<u>`
 * - `~~취소선~~`, `--취소선--` -> `<del>`
 * - `` `코드` `` -> `<code>` (내부는 리터럴로 취급, 재귀 파싱하지 않는다)
 * - `[[문서]]`, `[[문서|표시문구]]` -> 내부 링크 (`/wiki/{rawurlencode(title)}`)
 * - `[[http://...]]`, `[[http://... 표시문구]]`, `[http://...]`,
 *   `[http://... 표시문구]` -> 외부 링크
 *
 * XSS 안전: 원문에서 나온 모든 리터럴 텍스트는 `Escaper`로 이스케이프한
 * 뒤에만 태그로 감싼다. href 등 속성으로 들어가는 값도 이스케이프한다.
 * 굵게/기울임/밑줄/취소선의 내용은 중첩을 지원하기 위해 재귀적으로
 * 다시 파싱하지만, 코드와 링크 표시문구는 리터럴로만 처리한다 — 짝이 맞지
 * 않는 마크업(닫는 기호가 없는 경우)은 정규식이 매치하지 않으므로 자연히
 * 리터럴 텍스트로 남는다.
 */
final class InlineParser
{
    /**
     * 인라인 토큰 하나를 찾는 정규식. 왼쪽에서 가장 먼저 시작하는 토큰이
     * 항상 우선한다(PCRE leftmost matching).
     *
     * 굵게(''')/기울임('')처럼 구분자 문자를 공유하는 서로 다른 길이의
     * 런(run)에는 여는/닫는 구분자 양옆에 `(?<!x)`/`(?!x)`를 붙여 "정확히
     * 이 길이의 고립된 런"만 매치하도록 강제한다. 이 가드가 없으면
     * `'''`(굵게, 3개) 안의 처음 2개를 `''`(기울임, 2개)의 닫는 짝으로
     * 잘못 소비해 중첩 파싱이 깨진다.
     */
    private const TOKEN_PATTERN = <<<'REGEX'
/
    (?<!')'''(?!')(?<bold>.+?)(?<!')'''(?!')
    |(?<!')''(?!')(?<italic>.+?)(?<!')''(?!')
    |(?<!_)__(?!_)(?<underline>.+?)(?<!_)__(?!_)
    |(?<!~)~~(?!~)(?<strike>.+?)(?<!~)~~(?!~)
    |(?<!-)--(?!-)(?<strike2>.+?)(?<!-)--(?!-)
    |`(?<code>[^`]+?)`
    |\[\[(?<bracket>[^\[\]]+?)\]\]
    |\[(?<singleUrl>(?:https?|ftp):\/\/[^\s\]|]+)(?:[ \t|]+(?<singleLabel>[^\]]*))?\]
/xsui
REGEX;

    private const URL_SCHEME_PATTERN = '/^(?:https?|ftp):\/\//i';

    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 소스 텍스트의 인라인 문법을 HTML로 변환한다.
     */
    public function parse(string $source): InlineParseResult
    {
        $parsed = $this->parseInline($source);

        return new InlineParseResult($parsed['html'], $parsed['links']);
    }

    /**
     * @return array{html: string, links: list<string>}
     */
    private function parseInline(string $text): array
    {
        $html = '';
        $links = [];
        $offset = 0;
        $length = strlen($text);

        while ($offset < $length) {
            $matched = preg_match(
                self::TOKEN_PATTERN,
                $text,
                $matches,
                PREG_OFFSET_CAPTURE | PREG_UNMATCHED_AS_NULL,
                $offset
            );

            if ($matched !== 1) {
                $html .= $this->escaper->html(substr($text, $offset));
                break;
            }

            $matchStart = $matches[0][1];
            $matchText = $matches[0][0];

            if ($matchStart > $offset) {
                $html .= $this->escaper->html(substr($text, $offset, $matchStart - $offset));
            }

            $rendered = $this->renderMatch($matches);
            $html .= $rendered['html'];
            foreach ($rendered['links'] as $link) {
                $links[] = $link;
            }

            $offset = $matchStart + strlen($matchText);
        }

        return ['html' => $html, 'links' => $links];
    }

    /**
     * @param array<string, array{0: string|null, 1: int}> $matches
     * @return array{html: string, links: list<string>}
     */
    private function renderMatch(array $matches): array
    {
        if ($matches['bold'][0] !== null) {
            return $this->wrapRecursive('strong', $matches['bold'][0]);
        }

        if ($matches['italic'][0] !== null) {
            return $this->wrapRecursive('em', $matches['italic'][0]);
        }

        if ($matches['underline'][0] !== null) {
            return $this->wrapRecursive('u', $matches['underline'][0]);
        }

        if ($matches['strike'][0] !== null) {
            return $this->wrapRecursive('del', $matches['strike'][0]);
        }

        if ($matches['strike2'][0] !== null) {
            return $this->wrapRecursive('del', $matches['strike2'][0]);
        }

        if ($matches['code'][0] !== null) {
            $escaped = $this->escaper->html($matches['code'][0]);

            return ['html' => "<code>{$escaped}</code>", 'links' => []];
        }

        if ($matches['bracket'][0] !== null) {
            return $this->renderBracket($matches['bracket'][0]);
        }

        if ($matches['singleUrl'][0] !== null) {
            $label = $matches['singleLabel'][0] !== null ? trim($matches['singleLabel'][0]) : null;

            return $this->renderExternalLink($matches['singleUrl'][0], $label !== '' ? $label : null);
        }

        // TOKEN_PATTERN의 모든 대안은 named group을 하나씩 가지므로 도달 불가.
        throw new \LogicException('알 수 없는 인라인 토큰이 매치되었습니다.');
    }

    /**
     * 굵게/기울임/밑줄/취소선처럼 내용에 다른 인라인 마크업이 중첩될 수 있는
     * 구문을 처리한다 — 내용을 재귀적으로 다시 파싱한 뒤 태그로 감싼다.
     *
     * @return array{html: string, links: list<string>}
     */
    private function wrapRecursive(string $tag, string $innerSource): array
    {
        $inner = $this->parseInline($innerSource);

        return ['html' => "<{$tag}>{$inner['html']}</{$tag}>", 'links' => $inner['links']];
    }

    /**
     * `[[...]]` 대괄호 내용을 내부 링크 또는(URL로 시작하면) 외부 링크로
     * 렌더링한다.
     *
     * @return array{html: string, links: list<string>}
     */
    private function renderBracket(string $content): array
    {
        if (preg_match(self::URL_SCHEME_PATTERN, $content) === 1) {
            [$url, $label] = $this->splitUrlAndLabel($content);

            return $this->renderExternalLink($url, $label);
        }

        $pipePosition = strpos($content, '|');
        if ($pipePosition === false) {
            $title = trim($content);
            $label = null;
        } else {
            $title = trim(substr($content, 0, $pipePosition));
            $label = trim(substr($content, $pipePosition + 1));
        }

        return $this->renderInternalLink($title, $label !== null && $label !== '' ? $label : null);
    }

    /**
     * `[[http://url 표시문구]]` 형태에서 URL과 표시문구를 분리한다. 구분자로
     * 공백/탭 또는 `|`를 허용한다(표시문구가 없으면 null).
     *
     * @return array{0: string, 1: string|null}
     */
    private function splitUrlAndLabel(string $content): array
    {
        if (preg_match('/^([^\s|]+)[ \t|]+(.+)$/us', trim($content), $split) === 1) {
            $label = trim($split[2]);

            return [$split[1], $label !== '' ? $label : null];
        }

        return [trim($content), null];
    }

    /**
     * @return array{html: string, links: list<string>}
     */
    private function renderInternalLink(string $title, ?string $label): array
    {
        $href = '/wiki/' . rawurlencode($title);
        $escapedHref = $this->escaper->attribute($href);
        $escapedLabel = $this->escaper->html($label ?? $title);

        return [
            'html' => "<a href=\"{$escapedHref}\">{$escapedLabel}</a>",
            'links' => [$title],
        ];
    }

    /**
     * @return array{html: string, links: list<string>}
     */
    private function renderExternalLink(string $url, ?string $label): array
    {
        $escapedHref = $this->escaper->attribute($url);
        $escapedLabel = $this->escaper->html($label ?? $url);

        return [
            'html' => "<a href=\"{$escapedHref}\" rel=\"noopener noreferrer\">{$escapedLabel}</a>",
            'links' => [],
        ];
    }
}
