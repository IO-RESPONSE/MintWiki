<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;

/**
 * 문서 diff page의 서버 렌더링 (태스크 0535, 실제 diff 계산과 라우트 연결은 0710).
 *
 * 두 리비전의 source를 줄 단위로 비교해 변경사항을 보여준다. 렌더 결과(HTML)
 * 기준 diff가 아니라 저장된 원문(source) 기준 diff다(0710 Out of Scope).
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class DocumentDiffPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 diff page를 렌더링한다.
     *
     * @param Document $document 비교할 문서
     * @param Revision $fromRevision 비교 대상 이전 리비전
     * @param Revision $toRevision 비교 대상 이후 리비전
     */
    public function render(Document $document, Revision $fromRevision, Revision $toRevision): string
    {
        $title = $this->escaper->html($document->title());
        $fromRevisionId = $this->escaper->html($fromRevision->id());
        $toRevisionId = $this->escaper->html($toRevision->id());

        $body = '<main>'
            . '<h1>' . $title . ' - diff</h1>'
            . '<p>리비전 비교</p>'
            . '<p>From: ' . $fromRevisionId . '</p>'
            . '<p>To: ' . $toRevisionId . '</p>'
            . $this->renderDiff($fromRevision->source(), $toRevision->source())
            . '</main>';

        return $this->layout->render($title . ' - diff', $body);
    }

    /**
     * 두 source를 줄 단위로 비교한 결과를 렌더링한다.
     */
    private function renderDiff(string $fromSource, string $toSource): string
    {
        if ($fromSource === $toSource) {
            return '<p class="document-diff__empty">변경 사항이 없습니다.</p>';
        }

        $fromLines = $fromSource === '' ? [] : explode("\n", $fromSource);
        $toLines = $toSource === '' ? [] : explode("\n", $toSource);

        $html = '<ul class="document-diff">';
        foreach ($this->diffLines($fromLines, $toLines) as [$type, $line]) {
            $escapedLine = $this->escaper->html($line);
            $className = match ($type) {
                'added' => 'document-diff__line--added',
                'removed' => 'document-diff__line--removed',
                default => 'document-diff__line--unchanged',
            };
            $marker = match ($type) {
                'added' => '+',
                'removed' => '-',
                default => ' ',
            };
            $html .= '<li class="' . $className . '">' . $marker . ' ' . $escapedLine . '</li>';
        }
        $html .= '</ul>';

        return $html;
    }

    /**
     * 최장 공통 부분열(LCS) 기반의 라인 단위 최소 diff 구현.
     *
     * @param string[] $fromLines
     * @param string[] $toLines
     * @return array<int, array{0: string, 1: string}> [type, line] 튜플 목록.
     *         type은 'unchanged'/'removed'/'added' 중 하나다.
     */
    private function diffLines(array $fromLines, array $toLines): array
    {
        $fromCount = count($fromLines);
        $toCount = count($toLines);

        $lengths = array_fill(0, $fromCount + 1, array_fill(0, $toCount + 1, 0));
        for ($i = $fromCount - 1; $i >= 0; $i--) {
            for ($j = $toCount - 1; $j >= 0; $j--) {
                $lengths[$i][$j] = $fromLines[$i] === $toLines[$j]
                    ? $lengths[$i + 1][$j + 1] + 1
                    : max($lengths[$i + 1][$j], $lengths[$i][$j + 1]);
            }
        }

        $operations = [];
        $i = 0;
        $j = 0;
        while ($i < $fromCount && $j < $toCount) {
            if ($fromLines[$i] === $toLines[$j]) {
                $operations[] = ['unchanged', $fromLines[$i]];
                $i++;
                $j++;
            } elseif ($lengths[$i + 1][$j] >= $lengths[$i][$j + 1]) {
                $operations[] = ['removed', $fromLines[$i]];
                $i++;
            } else {
                $operations[] = ['added', $toLines[$j]];
                $j++;
            }
        }
        while ($i < $fromCount) {
            $operations[] = ['removed', $fromLines[$i]];
            $i++;
        }
        while ($j < $toCount) {
            $operations[] = ['added', $toLines[$j]];
            $j++;
        }

        return $operations;
    }
}
