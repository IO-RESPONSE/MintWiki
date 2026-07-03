<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 감사 행(row) 컴포넌트 (태스크 0573).
 *
 * 감사 이벤트 목록에서 각 행을 렌더링한다. 이벤트 유형, 행위자, 대상, 시간을 표시한다.
 * 모든 텍스트는 XSS 방지를 위해 escaping된다.
 */
final class AuditRow
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 감사 행을 렌더링한다.
     *
     * @param string $eventType 이벤트 유형 (module.action 형식 권장) (필수)
     * @param ?string $actor 행위자 ID (필수, null 불가)
     * @param string $target 대상 (문서명 등) (필수)
     * @param string $time 이벤트 시간 (필수, ISO 8601 형식 권장)
     * @return string 감사 행 HTML
     */
    public function render(string $eventType, ?string $actor, string $target, string $time): string
    {
        if (empty($eventType) || $actor === null || empty($target) || empty($time)) {
            return '';
        }

        $escapedEventType = $this->escaper->html($eventType);
        $escapedActor = $this->escaper->html($actor);
        $escapedTarget = $this->escaper->html($target);
        $escapedTime = $this->escaper->html($time);

        $html = '<tr class="audit-row">';
        $html .= '<td class="audit-row__event-type">' . $escapedEventType . '</td>';
        $html .= '<td class="audit-row__actor">' . $escapedActor . '</td>';
        $html .= '<td class="audit-row__target">' . $escapedTarget . '</td>';
        $html .= '<td class="audit-row__time">' . $escapedTime . '</td>';
        $html .= '</tr>';

        return $html;
    }

    /**
     * 감사 행 목록을 렌더링한다.
     *
     * @param array<array{eventType: string, actor: ?string, target: string, time: string}> $rows 감사 행 배열
     * @return string 감사 행 목록 HTML
     */
    public function renderTable(array $rows): string
    {
        if (empty($rows)) {
            return '';
        }

        $html = '<table class="audit-table">';
        $html .= '<thead>';
        $html .= '<tr>';
        $html .= '<th class="audit-table__header-event-type">이벤트</th>';
        $html .= '<th class="audit-table__header-actor">행위자</th>';
        $html .= '<th class="audit-table__header-target">대상</th>';
        $html .= '<th class="audit-table__header-time">시간</th>';
        $html .= '</tr>';
        $html .= '</thead>';
        $html .= '<tbody>';

        foreach ($rows as $row) {
            if (!isset($row['eventType']) || !isset($row['actor']) || !isset($row['target']) || !isset($row['time'])) {
                continue;
            }

            $eventType = (string) $row['eventType'];
            $actor = isset($row['actor']) ? (string) $row['actor'] : null;
            $target = (string) $row['target'];
            $time = (string) $row['time'];

            $html .= $this->render($eventType, $actor, $target, $time);
        }

        $html .= '</tbody>';
        $html .= '</table>';

        return $html;
    }
}
