<?php

declare(strict_types=1);

/**
 * UI DB 연기 테스트(smoke test). 문서 생성/조회 DB round-trip을 검증한다(태스크 0605).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 데이터가 데이터베이스에
 * 올바르게 저장되고 검색되는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Modules\Document\Document;

$failures = [];

// in-memory SQLite 데이터베이스 생성
try {
    $connection = new PDO('sqlite::memory:', null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (Exception $e) {
    $failures[] = 'SQLite 데이터베이스 생성 실패: ' . $e->getMessage();
    goto output;
}

// (1) document 테이블 스키마 생성
try {
    $connection->exec('
        CREATE TABLE document (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            current_revision_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ');
} catch (Exception $e) {
    $failures[] = 'document 테이블 생성 실패: ' . $e->getMessage();
    goto output;
}

// (2) 문서 데이터 생성 및 삽입
$docId = 'doc-smoke-001';
$title = 'DB Round-Trip Test Document';
$normalizedTitle = strtolower(trim($title));
$now = date('Y-m-d H:i:s');

try {
    $stmt = $connection->prepare('
        INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ');
    $stmt->execute([
        $docId,
        $title,
        $normalizedTitle,
        null,
        $now,
        $now
    ]);
} catch (Exception $e) {
    $failures[] = '문서 삽입 실패: ' . $e->getMessage();
    goto output;
}

// (3) id로 문서 조회
$retrieved = null;
try {
    $stmt = $connection->prepare('SELECT * FROM document WHERE id = ?');
    $stmt->execute([$docId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row) {
        $retrieved = new Document(
            id: $row['id'],
            title: $row['title'],
            normalized_title: $row['normalized_title'],
            current_revision_id: $row['current_revision_id']
        );
    }
} catch (Exception $e) {
    $failures[] = 'id로 문서 조회 실패: ' . $e->getMessage();
    goto output;
}

// (4) 조회 결과 검증 - id
if ($retrieved === null) {
    $failures[] = 'id로 조회한 문서가 null이다.';
} else {
    if ($retrieved->id !== $docId) {
        $failures[] = '조회한 문서의 id가 일치하지 않는다.';
    }

    // (5) 조회 결과 검증 - title
    if ($retrieved->title !== $title) {
        $failures[] = '조회한 문서의 title이 일치하지 않는다.';
    }

    // (6) 조회 결과 검증 - normalized_title
    if ($retrieved->normalized_title !== $normalizedTitle) {
        $failures[] = '조회한 문서의 normalized_title이 일치하지 않는다.';
    }

    // (7) 조회 결과 검증 - current_revision_id
    if ($retrieved->current_revision_id !== null) {
        $failures[] = '조회한 문서의 current_revision_id가 null이어야 한다.';
    }
}

// (8) normalized_title로 문서 조회
$retrievedByTitle = null;
try {
    $stmt = $connection->prepare('SELECT * FROM document WHERE normalized_title = ?');
    $stmt->execute([$normalizedTitle]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row) {
        $retrievedByTitle = new Document(
            id: $row['id'],
            title: $row['title'],
            normalized_title: $row['normalized_title'],
            current_revision_id: $row['current_revision_id']
        );
    }
} catch (Exception $e) {
    $failures[] = 'normalized_title로 문서 조회 실패: ' . $e->getMessage();
    goto output;
}

// (9) normalized_title 조회 결과 검증
if ($retrievedByTitle === null) {
    $failures[] = 'normalized_title로 조회한 문서가 null이다.';
} else {
    if ($retrievedByTitle->id !== $docId) {
        $failures[] = 'normalized_title로 조회한 문서의 id가 일치하지 않는다.';
    }
    if ($retrievedByTitle->title !== $title) {
        $failures[] = 'normalized_title로 조회한 문서의 title이 일치하지 않는다.';
    }
}

// (10) 여러 문서 생성 및 각각 조회 가능
$doc2Id = 'doc-smoke-002';
$doc2Title = 'Another Document';
$doc2NormalizedTitle = strtolower(trim($doc2Title));

try {
    $stmt = $connection->prepare('
        INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ');
    $stmt->execute([
        $doc2Id,
        $doc2Title,
        $doc2NormalizedTitle,
        null,
        $now,
        $now
    ]);

    // 첫 번째 문서 조회 확인
    $stmt = $connection->prepare('SELECT id FROM document WHERE id = ?');
    $stmt->execute([$docId]);
    if (!$stmt->fetch(PDO::FETCH_ASSOC)) {
        $failures[] = '두 번째 문서 생성 후 첫 번째 문서가 조회되지 않는다.';
    }

    // 두 번째 문서 조회 확인
    $stmt = $connection->prepare('SELECT id FROM document WHERE id = ?');
    $stmt->execute([$doc2Id]);
    if (!$stmt->fetch(PDO::FETCH_ASSOC)) {
        $failures[] = '두 번째 문서가 조회되지 않는다.';
    }
} catch (Exception $e) {
    $failures[] = '여러 문서 생성 실패: ' . $e->getMessage();
    goto output;
}

// (11) 문서 업데이트 및 round-trip 검증
$newTitle = 'Updated Document Title';
$newNormalizedTitle = strtolower(trim($newTitle));
$newUpdatedAt = date('Y-m-d H:i:s');

try {
    $stmt = $connection->prepare('
        UPDATE document
        SET title = ?, normalized_title = ?, updated_at = ?
        WHERE id = ?
    ');
    $stmt->execute([
        $newTitle,
        $newNormalizedTitle,
        $newUpdatedAt,
        $docId
    ]);

    // 업데이트된 문서 조회
    $stmt = $connection->prepare('SELECT * FROM document WHERE id = ?');
    $stmt->execute([$docId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$row || $row['title'] !== $newTitle) {
        $failures[] = '업데이트된 title이 조회되지 않는다.';
    }
    if (!$row || $row['normalized_title'] !== $newNormalizedTitle) {
        $failures[] = '업데이트된 normalized_title이 조회되지 않는다.';
    }
} catch (Exception $e) {
    $failures[] = '문서 업데이트 실패: ' . $e->getMessage();
    goto output;
}

// (12) 존재하지 않는 문서 조회는 null 반환
try {
    $stmt = $connection->prepare('SELECT * FROM document WHERE id = ?');
    $stmt->execute(['nonexistent-doc']);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row !== false && $row !== null) {
        $failures[] = '존재하지 않는 문서 조회 시 null이 아닌 값을 반환한다.';
    }
} catch (Exception $e) {
    $failures[] = '존재하지 않는 문서 조회 실패: ' . $e->getMessage();
    goto output;
}

output:

if ($failures !== []) {
    fwrite(STDERR, "UI DB 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI DB 연기 테스트 통과.\n");
exit(0);
