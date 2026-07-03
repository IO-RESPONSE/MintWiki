<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * UI i18n 지원을 위한 placeholder.
 *
 * 기본 locale은 'ko'이며, 향후 실제 번역 로직으로 확장할 수 있다.
 */
final class I18n
{
    private string $locale;

    public function __construct(string $locale = 'ko')
    {
        $this->locale = $locale;
    }

    /**
     * 현재 locale을 반환한다.
     */
    public function getLocale(): string
    {
        return $this->locale;
    }

    /**
     * locale을 설정한다.
     */
    public function setLocale(string $locale): void
    {
        $this->locale = $locale;
    }

    /**
     * 주어진 key를 번역한다.
     *
     * 현재는 placeholder로 key를 그대로 반환한다.
     * 향후 실제 번역 로직이 추가될 수 있다.
     *
     * @param string $key 번역할 key
     * @param array<string, string> $params 번역 문자열 내 치환할 parameter
     */
    public function t(string $key, array $params = []): string
    {
        $translated = $key;

        foreach ($params as $name => $value) {
            $translated = str_replace(':' . $name, $value, $translated);
        }

        return $translated;
    }
}
