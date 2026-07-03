<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 최근 변경 행(row) 컴포넌트 (태스크 0572).
 *
 * 최근 변경 목록에서 각 행을 렌더링한다. 문서명, 사용자, 요약, 시간을 표시한다.
 * 모든 텍스트는 XSS 방지를 위해 escaping된다.
 */
final class RecentChangesRow
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 최근 변경 행을 렌더링한다.
     *
     * @param string $documentName 문서명 (필수)
     * @param string $user 변경을 수행한 사용자 ID (필수)
     * @param string $summary 변경 요약 (필수)
     * @param string $time 변경 시간 (필수, ISO 8601 형식 권장)
     * @return string 최근 변경 행 HTML
     */
    public function render(string $documentName, string $user, string $summary, string $time): string
    {
        if (empty($documentName) || empty($user) || empty($summary) || empty($time)) {
            return '';
        }

        $escapedDocumentName = $this->escaper->html($documentName);
        $escapedUser = $this->escaper->html($user);
        $escapedSummary = $this->escaper->html($summary);
        $escapedTime = $this->escaper->html($time);

        $html = '<tr class="recent-changes-row">';
        $html .= '<td class="recent-changes-row__document">' . $escapedDocumentName . '</td>';
        $html .= '<td class="recent-changes-row__user">' . $escapedUser . '</td>';
        $html .= '<td class="recent-changes-row__summary">' . $escapedSummary . '</td>';
        $html .= '<td class="recent-changes-row__time">' . $escapedTime . '</td>';
        $html .= '</tr>';

        return $html;
    }

    /**
     * 최근 변경 행 목록을 렌더링한다.
     *
     * @param array<array{documentName: string, user: string, summary: string, time: string}> $rows 최근 변경 행 배열
     * @return string 최근 변경 행 목록 HTML
     */
    public function renderTable(array $rows): string
    {
        if (empty($rows)) {
            return '';
        }

        $html = '<table class="recent-changes-table">';
        $html .= '<thead>';
        $html .= '<tr>';
        $html .= '<th class="recent-changes-table__header-document">문서</th>';
        $html .= '<th class="recent-changes-table__header-user">사용자</th>';
        $html .= '<th class="recent-changes-table__header-summary">요약</th>';
        $html .= '<th class="recent-changes-table__header-time">시간</th>';
        $html .= '</tr>';
        $html .= '</thead>';
        $html .= '<tbody>';

        foreach ($rows as $row) {
            if (!isset($row['documentName']) || !isset($row['user']) || !isset($row['summary']) || !isset($row['time'])) {
                continue;
            }

            $documentName = (string) $row['documentName'];
            $user = (string) $row['user'];
            $summary = (string) $row['summary'];
            $time = (string) $row['time'];

            $html .= $this->render($documentName, $user, $summary, $time);
        }

        $html .= '</tbody>';
        $html .= '</table>';

        return $html;
    }
}
