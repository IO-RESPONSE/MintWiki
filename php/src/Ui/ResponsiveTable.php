<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 반응형 테이블 컴포넌트 (태스크 0551).
 *
 * 모바일/데스크톱에 반응하는 테이블을 렌더링한다.
 * 감사 로그, 최근 변경, 관리자 목록 등에서 재사용 가능하다.
 * 모든 셀 데이터는 XSS 방지를 위해 escaping된다.
 */
final class ResponsiveTable
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 반응형 테이블을 렌더링한다.
     *
     * @param array<array{key: string, label: string}> $columns 컬럼 정의 (key: 데이터 키, label: 헤더 텍스트)
     * @param array<array<string, string>> $rows 테이블 데이터
     * @param string|null $caption 테이블 캡션 (선택사항)
     */
    public function render(array $columns, array $rows, ?string $caption = null): string
    {
        if (empty($columns)) {
            return '';
        }

        $html = '<div class="responsive-table-wrapper">';
        $html .= '<table class="responsive-table">';

        // 캡션 추가
        if ($caption !== null) {
            $escapedCaption = $this->escaper->html($caption);
            $html .= '<caption>' . $escapedCaption . '</caption>';
        }

        // 테이블 헤더
        $html .= $this->renderTableHeader($columns);

        // 테이블 바디
        $html .= $this->renderTableBody($columns, $rows);

        $html .= '</table>';
        $html .= '</div>';

        return $html;
    }

    /**
     * 테이블 헤더를 렌더링한다.
     *
     * @param array<array{key: string, label: string}> $columns
     */
    private function renderTableHeader(array $columns): string
    {
        $html = '<thead>';
        $html .= '<tr>';

        foreach ($columns as $column) {
            $label = $this->escaper->html($column['label']);
            $html .= '<th scope="col">' . $label . '</th>';
        }

        $html .= '</tr>';
        $html .= '</thead>';

        return $html;
    }

    /**
     * 테이블 바디를 렌더링한다.
     *
     * @param array<array{key: string, label: string}> $columns
     * @param array<array<string, string>> $rows
     */
    private function renderTableBody(array $columns, array $rows): string
    {
        if (empty($rows)) {
            return '<tbody></tbody>';
        }

        $html = '<tbody>';

        foreach ($rows as $row) {
            $html .= '<tr>';

            foreach ($columns as $column) {
                $key = $column['key'];
                $value = $row[$key] ?? '';
                $escapedValue = $this->escaper->html((string) $value);
                $html .= '<td data-column="' . $this->escaper->html($key) . '">' . $escapedValue . '</td>';
            }

            $html .= '</tr>';
        }

        $html .= '</tbody>';

        return $html;
    }
}
