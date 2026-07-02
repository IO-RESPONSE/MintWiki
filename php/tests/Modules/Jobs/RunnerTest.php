<?php

declare(strict_types=1);

/**
 * MintWiki\Jobs\Runner 포트의 시그니처와 shared hosting sync fallback 계약을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0411
 * Cache/BackendTest.php와 동일한 방식).
 *
 * 태스크 0412는 구현 없이 port만 추가하므로, 이 테스트는 실제 잡 러너
 * 동작이 아니라 (1) 인터페이스가 계약대로 구현 가능한지 — 익명 클래스로
 * 구현해 본다 — 와 (2) enqueue가 워커 없이도 runSync에 위임해 동기적으로
 * 처리를 끝낼 수 있다는 shared hosting fallback 시나리오만 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Jobs\Runner;

$failures = [];

if (!interface_exists(Runner::class)) {
    $failures[] = 'MintWiki\\Jobs\\Runner는 interface여야 한다.';
}

// 큐 백엔드 없이 enqueue()가 runSync()에 위임해 즉시 처리를 끝내는
// shared hosting sync fallback 구현.
$runner = new class implements Runner {
    /** @var array<string, mixed> */
    private array $results = [];

    private int $counter = 0;

    public function enqueue(mixed $payload): string
    {
        $jobId = 'job-' . (++$this->counter);
        $this->results[$jobId] = $this->runSync($payload);

        return $jobId;
    }

    public function runSync(mixed $payload): mixed
    {
        return ['echo' => $payload];
    }

    public function getStatus(string $jobId): mixed
    {
        return $this->results[$jobId] ?? null;
    }
};

if ($runner->runSync(['task' => 'reindex']) !== ['echo' => ['task' => 'reindex']]) {
    $failures[] = 'runSync()은 워커 없이 곧바로 잡을 실행하고 결과를 반환해야 한다.';
}

if ($runner->getStatus('never-enqueued') !== null) {
    $failures[] = 'getStatus()는 등록된 적 없는 jobId에 대해 null을 반환해야 한다.';
}

$firstJobId = $runner->enqueue(['task' => 'purge-cache']);
$secondJobId = $runner->enqueue(['task' => 'refresh-index']);

if ($firstJobId === '' || $secondJobId === '') {
    $failures[] = 'enqueue()는 비어있지 않은 job id를 반환해야 한다.';
}

if ($firstJobId === $secondJobId) {
    $failures[] = 'enqueue()는 호출마다 서로 다른 job id를 반환해야 한다.';
}

if ($runner->getStatus($firstJobId) !== ['echo' => ['task' => 'purge-cache']]) {
    $failures[] = 'getStatus()는 enqueue()가 sync fallback으로 즉시 처리한 결과를 조회할 수 있어야 한다.';
}

if ($runner->getStatus($secondJobId) !== ['echo' => ['task' => 'refresh-index']]) {
    $failures[] = 'getStatus()는 각 job id별로 독립된 결과를 조회할 수 있어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Runner 포트 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Runner 포트 테스트 통과.\n");
exit(0);
