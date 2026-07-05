<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 파일 권한 진단 page의 서버 렌더링 (태스크 0631).
 *
 * 공유 호스팅 배포에서 확인해야 하는 설정 파일과 쓰기 디렉터리의 권한 상태를
 * 표시한다. 실제 파일 시스템 검사는 이후 어댑터가 전달하는 진단 rows로 분리한다.
 */
final class FilePermissionDiagnosticsPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 파일 권한 진단 page를 렌더링한다.
     *
     * @param array<int, array{label: string, path: string, expected: string, status: string, detail: string}>|null $diagnostics 파일 권한 진단 rows
     */
    public function render(?array $diagnostics = null): string
    {
        $rows = $diagnostics ?? $this->defaultDiagnostics();

        $body = '<main>'
            . '<h1>파일 권한 진단</h1>'
            . '<p>공유 호스팅 배포에 필요한 파일과 디렉터리 권한 상태를 확인합니다.</p>'
            . '<p><a href="/admin/diagnostics">운영 진단으로 돌아가기</a></p>'
            . $this->renderDiagnosticsTable($rows)
            . '</main>';

        return $this->layout->render('파일 권한 진단', $body);
    }

    /**
     * 기본 파일 권한 진단 rows를 반환한다.
     *
     * @return array<int, array{label: string, path: string, expected: string, status: string, detail: string}>
     */
    private function defaultDiagnostics(): array
    {
        return [
            [
                'label' => '설정 파일',
                'path' => 'php/config/local.php',
                'expected' => '웹 서버 쓰기 금지',
                'status' => '검사 대기',
                'detail' => '설치 후 설정 파일은 읽기 전용으로 제한해야 합니다.',
            ],
            [
                'label' => '캐시 디렉터리',
                'path' => 'var/cache',
                'expected' => '웹 서버 쓰기 허용',
                'status' => '검사 대기',
                'detail' => '페이지 캐시와 임시 렌더링 결과를 저장할 수 있어야 합니다.',
            ],
            [
                'label' => '업로드 디렉터리',
                'path' => 'var/uploads',
                'expected' => '웹 서버 쓰기 허용',
                'status' => '검사 대기',
                'detail' => '첨부 파일 저장을 위해 쓰기 권한이 필요합니다.',
            ],
            [
                'label' => '로그 디렉터리',
                'path' => 'var/log',
                'expected' => '웹 서버 쓰기 허용',
                'status' => '검사 대기',
                'detail' => '운영 로그와 진단 로그를 남길 수 있어야 합니다.',
            ],
        ];
    }

    /**
     * 파일 권한 진단 표를 렌더링한다.
     *
     * @param array<int, array{label: string, path: string, expected: string, status: string, detail: string}> $diagnostics 파일 권한 진단 rows
     */
    private function renderDiagnosticsTable(array $diagnostics): string
    {
        $html = '<section aria-label="파일 권한 상태">'
            . '<h2>권한 상태</h2>'
            . '<table>'
            . '<thead><tr>'
            . '<th scope="col">대상</th>'
            . '<th scope="col">경로</th>'
            . '<th scope="col">권장 권한</th>'
            . '<th scope="col">상태</th>'
            . '<th scope="col">설명</th>'
            . '</tr></thead>'
            . '<tbody>';

        foreach ($diagnostics as $diagnostic) {
            $html .= '<tr>'
                . '<th scope="row">' . $this->escaper->html($diagnostic['label']) . '</th>'
                . '<td><code>' . $this->escaper->html($diagnostic['path']) . '</code></td>'
                . '<td>' . $this->escaper->html($diagnostic['expected']) . '</td>'
                . '<td>' . $this->escaper->html($diagnostic['status']) . '</td>'
                . '<td>' . $this->escaper->html($diagnostic['detail']) . '</td>'
                . '</tr>';
        }

        return $html . '</tbody></table></section>';
    }
}
