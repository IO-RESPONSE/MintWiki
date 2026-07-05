<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Audit\AuditEventRecord;

/**
 * 감사 로그 viewer page의 서버 렌더링 (태스크 0545, `GET /admin/audit` 배선과
 * 실데이터(`RecentAuditEventsQuery`) 주입은 0698).
 *
 * 이벤트 목록이 있으면 `AuditRow`로 표를 렌더링하고, 없으면 빈 상태를
 * 표시한다. 필터/CSV export 영역은 0698 범위 밖이라 placeholder를 그대로
 * 둔다. 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class AuditViewerPage
{
    private Escaper $escaper;
    private Layout $layout;
    private AuditRow $auditRow;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->auditRow = new AuditRow($this->escaper);
    }

    /**
     * 감사 로그 page를 렌더링한다.
     *
     * @param AuditEventRecord[] $auditEvents 최근순으로 정렬된 감사 이벤트 목록, 없으면 빈 배열
     */
    public function render(array $auditEvents = []): string
    {
        $filterArea = $this->renderFilterArea();
        $exportAction = $this->renderExportAction();
        $eventsSection = $this->renderEventsSection($auditEvents);

        $body = '<main>'
            . '<h1>감사 로그</h1>'
            . $filterArea
            . $exportAction
            . $eventsSection
            . '</main>';

        return $this->layout->render('감사 로그', $body);
    }

    /**
     * 필터 영역을 렌더링한다.
     */
    private function renderFilterArea(): string
    {
        return '<section aria-label="필터">'
            . '<p>필터</p>'
            . '</section>';
    }

    /**
     * export 액션 영역을 렌더링한다.
     */
    private function renderExportAction(): string
    {
        return '<section aria-label="export 액션">'
            . '<button class="audit-export-button" aria-label="감사 로그를 CSV로 export">CSV로 export (준비 중)</button>'
            . '</section>';
    }

    /**
     * 감사 로그 목록 영역을 렌더링한다. 이벤트가 없으면 빈 상태 메시지를,
     * 있으면 `AuditRow`로 만든 표를 보여준다.
     *
     * @param AuditEventRecord[] $auditEvents
     */
    private function renderEventsSection(array $auditEvents): string
    {
        $content = $auditEvents === []
            ? '<p>감사 로그가 없습니다.</p>'
            : $this->auditRow->renderTable(array_map(
                [$this, 'toRowData'],
                $auditEvents
            ));

        return '<section aria-label="감사 로그 목록">' . $content . '</section>';
    }

    /**
     * `AuditEventRecord`를 `AuditRow::renderTable()`이 기대하는 행 데이터로 변환한다.
     * actor_id는 nullable이지만(db/schema/audit_event.sql) `AuditRow`는 null 행위자
     * 행을 건너뛰므로, 시스템이 기록한 이벤트도 표에서 누락되지 않게 대체 값을 채운다.
     *
     * @return array{eventType: string, actor: string, target: string, time: string}
     */
    private function toRowData(AuditEventRecord $event): array
    {
        return [
            'eventType' => $event->category() . '.' . $event->action(),
            'actor' => $event->actorId() ?? '시스템',
            'target' => $event->entityId(),
            'time' => $event->occurredAt(),
        ];
    }
}
