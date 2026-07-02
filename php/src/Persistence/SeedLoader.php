<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

use PDO;
use RuntimeException;

/**
 * Portable seed fixture 로더.
 *
 * ANSI SQL 기반의 INSERT 문을 파싱하여 데이터베이스에 로드한다.
 * PostgreSQL과 MariaDB 양쪽에서 동일하게 동작한다.
 */
class SeedLoader
{
    private string $fixturesDir;

    /**
     * 초기화.
     *
     * @param string|null $fixturesDir seed 파일들이 있는 디렉토리.
     *                                   지정하지 않으면 php/tests/fixtures/seed를 사용.
     */
    public function __construct(?string $fixturesDir = null)
    {
        if ($fixturesDir === null) {
            // 기본값: php/tests/fixtures/seed
            // 이 클래스가 php/src/Persistence에 있으므로 상대 경로로 접근
            $projectRoot = dirname(__DIR__, 2);
            $fixturesDir = $projectRoot . '/tests/fixtures/seed';
        }

        if (!is_dir($fixturesDir)) {
            throw new RuntimeException(
                "Fixtures 디렉토리를 찾을 수 없습니다: {$fixturesDir}"
            );
        }

        $this->fixturesDir = $fixturesDir;
    }

    /**
     * 특정 테이블의 seed 데이터를 로드한다.
     *
     * @param PDO $connection PDO 연결
     * @param string $tableName 로드할 테이블명 (파일명으로도 사용: {table_name}.sql)
     */
    public function loadSeed(PDO $connection, string $tableName): void
    {
        $sqlFile = $this->fixturesDir . '/' . $tableName . '.sql';

        if (!file_exists($sqlFile)) {
            throw new RuntimeException(
                "Seed 파일을 찾을 수 없습니다: {$sqlFile}"
            );
        }

        $sqlContent = file_get_contents($sqlFile);
        if ($sqlContent === false) {
            throw new RuntimeException(
                "Seed 파일을 읽을 수 없습니다: {$sqlFile}"
            );
        }

        // INSERT 문 파싱 및 실행
        $insertStatements = $this->parseInsertStatements($sqlContent);

        foreach ($insertStatements as $insertSql) {
            $connection->exec($insertSql);
        }
    }

    /**
     * 모든 seed 파일을 로드한다.
     *
     * 파일 순서대로 로드되므로, FK 종속성을 고려하여 파일명을 정렬할 것.
     *
     * @param PDO $connection PDO 연결
     */
    public function loadAllSeeds(PDO $connection): void
    {
        $files = scandir($this->fixturesDir);
        if ($files === false) {
            throw new RuntimeException(
                "Fixtures 디렉토리를 읽을 수 없습니다: {$this->fixturesDir}"
            );
        }

        // 숨김 파일과 디렉토리 제거
        $sqlFiles = array_filter($files, function (string $file): bool {
            return !str_starts_with($file, '.') && str_ends_with($file, '.sql');
        });

        // 정렬
        sort($sqlFiles);

        foreach ($sqlFiles as $sqlFile) {
            $tableName = pathinfo($sqlFile, PATHINFO_FILENAME);
            $this->loadSeed($connection, $tableName);
        }
    }

    /**
     * SQL 콘텐츠에서 INSERT 문들을 추출한다.
     *
     * @param string $sqlContent SQL 파일의 전체 내용
     * @return string[] INSERT 문 리스트 (주석 제거, 완전한 문)
     */
    private function parseInsertStatements(string $sqlContent): array
    {
        // 라인 주석 제거 (-- 이후의 모든 내용)
        $lines = explode("\n", $sqlContent);
        $cleanedLines = [];

        foreach ($lines as $line) {
            $line = preg_replace('/--.*$/', '', $line);
            $cleanedLines[] = $line;
        }

        $sqlContent = implode("\n", $cleanedLines);

        // 블록 주석 제거 (/* ... */)
        $sqlContent = preg_replace('/\/\*.*?\*\//s', '', $sqlContent);

        // INSERT 문 추출
        // INSERT INTO ... VALUES (...); 패턴
        $pattern = '/INSERT\s+INTO\s+\w+\s*\([^)]*\)\s*VALUES\s*\([^)]*\)\s*;/i';
        $matches = [];
        preg_match_all($pattern, $sqlContent, $matches);

        return $matches[0];
    }

    /**
     * Fixtures 디렉토리를 반환한다.
     *
     * @return string
     */
    public function getFixturesDir(): string
    {
        return $this->fixturesDir;
    }
}
