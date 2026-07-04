<?php

declare(strict_types=1);

namespace MintWiki\User;

use PDO;

/**
 * `account` 테이블에 대한 최소 영속화 (태스크 0681).
 *
 * User 모듈은 지금까지 `User`/`AnonymousIdentity`/`IpIdentity` 같은 식별자
 * value object만 가지고 있었고 DB 영속화가 없었다. 설치 마법사가 최초
 * 관리자 계정을 생성하려면 최소한의 쓰기/조회가 필요해 이 클래스를 추가한다.
 * 전체 `UserRepository` 포트 구현(`docs/repository-port-contracts.md`)은
 * 범위 밖이며, 여기서는 설치 단계에 필요한 두 동작만 제공한다.
 */
final class AccountRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * 주어진 username을 가진 계정이 이미 존재하는지 확인한다.
     */
    public function usernameExists(string $username): bool
    {
        $statement = $this->connection->prepare('SELECT 1 FROM account WHERE username = :username');
        $statement->execute(['username' => $username]);

        return $statement->fetchColumn() !== false;
    }

    /**
     * 새 계정을 생성하고 발급한 id를 반환한다.
     *
     * 비밀번호는 호출자가 이미 해시한 값(`password_hash()` 등)을 그대로
     * 저장한다 — 평문 비밀번호는 이 클래스에 닿지 않는다.
     */
    public function create(string $username, string $passwordHash, ?string $displayName = null): string
    {
        $id = self::generateId();

        $statement = $this->connection->prepare(
            'INSERT INTO account (id, username, display_name, password_hash) '
            . 'VALUES (:id, :username, :display_name, :password_hash)'
        );
        $statement->execute([
            'id' => $id,
            'username' => $username,
            'display_name' => $displayName,
            'password_hash' => $passwordHash,
        ]);

        return $id;
    }

    /**
     * UUID v4 문자열을 생성한다 (계정 id 발급용, `Document\Service`와 동일한 방식).
     */
    private static function generateId(): string
    {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
        $hex = bin2hex($bytes);

        return sprintf(
            '%s-%s-%s-%s-%s',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 12, 4),
            substr($hex, 16, 4),
            substr($hex, 20, 12)
        );
    }
}
