<?php

declare(strict_types=1);

namespace MintWiki\Jobs;

/**
 * 잡 실행 포트 (태스크 0412).
 *
 * jobs 모듈은 cache/document 등과 달리 Python 쪽에 아직 어떤 구현 파일도
 * 없다 — `src/modules/jobs`에는 README.md와 `manifest.json`만 존재하며,
 * `manifest.json`의 `service.public_methods`(enqueue/run_sync/get_status)와
 * `repository.interface`(JobRepository)는 모두 실제 코드가 아니라 이후
 * Python 태스크(0291-0339, 아직 미실행)가 구현해야 할 목표 계약일 뿐이다.
 * 그래서 이 인터페이스는 기존 Python ABC를 그대로 옮긴 것이 아니라,
 * `manifest.json`이 이미 이름을 고정한 세 메서드(enqueue/run_sync/get_status)를
 * PHP 쪽에서 먼저 계약으로 굳힌 것이다 — Python 구현이 이 이름과 달라지면
 * `manifest.json`과 이 파일을 함께 갱신해야 한다.
 *
 * `manifest.json`의 contract_notes가 명시하는 shared hosting 제약 —
 * 크론이나 별도 워커 프로세스를 붙일 수 없는 공유 호스팅에서는 큐 기반
 * 러너 대신 sync 러너가 기본 동작이어야 한다 — 을 반영해, `enqueue()`는
 * 별도 워커 없이도 호출된 요청/응답 사이클 안에서 `runSync()`를 즉시
 * 실행해 처리를 끝낼 수 있어야 한다. 큐를 실제로 사용하는 구현체는 이
 * 기본 동작 위에 얹는 선택적 개선일 뿐, sync 경로가 항상 최소 기준선이다.
 *
 * `JobPayload`/`JobResult`/`JobStatus`(Python 쪽에서도 아직 만들어지지
 * 않은 계획된 모델)가 PHP로 포팅되지 않았으므로, Cache\Backend와 같은
 * 이유로 payload/결과/상태 타입은 모두 `mixed`로 둔다. 잡을 저장소에
 * 영속화하는 책임(`manifest.json`의 `repository.interface: JobRepository`)은
 * 아직 메서드 시그니처가 어디에도 고정되어 있지 않아 이 태스크의 범위 밖이며,
 * 이후 태스크에서 별도 포트로 추가된다.
 */
interface Runner
{
    /**
     * 잡을 큐에 등록한다. 큐 백엔드가 없는 shared hosting 환경에서는
     * 구현체가 이 안에서 곧바로 runSync()를 호출해 동기적으로 처리를
     * 끝내도 된다 — 두 경우 모두 이후 getStatus()로 조회 가능한 job id를
     * 반환해야 한다.
     */
    public function enqueue(mixed $payload): string;

    /**
     * 잡을 호출한 요청/응답 사이클 안에서 즉시 실행하고 결과를 반환한다.
     */
    public function runSync(mixed $payload): mixed;

    /**
     * jobId로 식별되는 잡의 현재 상태(또는 결과)를 조회한다. 알 수 없는
     * jobId에 대해서는 구현체가 null 등 "없음"을 나타내는 값을 반환한다.
     */
    public function getStatus(string $jobId): mixed;
}
