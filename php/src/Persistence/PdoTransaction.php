<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

use PDO;

/**
 * PDO 연결 위에 begin/commit/rollback만 노출하는 트랜잭션 wrapper (태스크 0485).
 *
 * `docs/db-adapter-contract.md` §2가 정한 최소 동작 집합 중 commit()과
 * rollback()은 이름까지 계약으로 고정되어 있다. begin()은 그 트랜잭션
 * 경계를 여는 대칭 동작으로 함께 둔다 — 이 클래스는 그 세 가지 계약
 * 이상을 다루지 않는다. add/fetch_one/fetch_all/execute에 해당하는 실제
 * statement 실행은 이후 Repository 골격 태스크의 책임이다.
 *
 * `PdoConnectionFactory`와 마찬가지로 §1(연결/세션 소유권)에 따라 연결을
 * 스스로 만들거나 닫지 않는다 — 생성자에 주입된 `PDO` 인스턴스를 감쌀
 * 뿐이다.
 */
final class PdoTransaction
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * 트랜잭션을 시작한다. `PDO::beginTransaction()`을 그대로 위임한다.
     */
    public function begin(): void
    {
        $this->connection->beginTransaction();
    }

    /**
     * 지금까지의 변경을 확정한다. 실패(제약 위반 등)하면 `PDOException`이
     * 그대로 전파된다 — §3의 통합 위반 신호로의 변환은 이 클래스가 아니라
     * Repository 계층의 책임이다.
     */
    public function commit(): void
    {
        $this->connection->commit();
    }

    /**
     * 지금까지의 변경을 취소한다. `PDO::rollBack()`을 그대로 위임한다.
     */
    public function rollback(): void
    {
        $this->connection->rollBack();
    }
}
