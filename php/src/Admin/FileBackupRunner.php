<?php

declare(strict_types=1);

namespace MintWiki\Admin;

/**
 * 공유 호스팅에서 동작 가능한 최소 백업 실행기.
 *
 * 현재 단계에서는 DB를 덤프/복원하지 않고, 백업 아티팩트 생성과 복원 파일
 * 접수만 수행한다. 파괴적인 실제 복원은 이후 운영 런북/DB 어댑터 작업에서
 * 이 인터페이스 뒤에 붙인다.
 */
final class FileBackupRunner implements BackupRunner
{
    public function __construct(private readonly string $backupDirectory)
    {
    }

    public function createBackup(): string
    {
        $this->ensureBackupDirectory();

        $name = 'mintwiki-backup-' . gmdate('Ymd-His') . '-' . bin2hex(random_bytes(4)) . '.json';
        $path = $this->backupDirectory . '/' . $name;
        $payload = [
            'app' => 'MintWiki',
            'created_at' => gmdate('c'),
            'type' => 'metadata-only',
        ];

        if (file_put_contents($path, json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n", LOCK_EX) === false) {
            throw new \RuntimeException('백업 파일을 생성할 수 없습니다.');
        }

        return $name;
    }

    public function listBackups(): array
    {
        if (!is_dir($this->backupDirectory)) {
            return [];
        }

        $items = scandir($this->backupDirectory);
        if ($items === false) {
            return [];
        }

        $backups = [];
        foreach ($items as $item) {
            if ($item === '.' || $item === '..') {
                continue;
            }
            $path = $this->backupDirectory . '/' . $item;
            if (is_file($path) && preg_match('/\.(json|sql)\z/i', $item) === 1) {
                $backups[] = $item;
            }
        }

        rsort($backups, SORT_STRING);

        return $backups;
    }

    /**
     * 다운로드 요청 파일명이 실제 백업 목록에 있는 안전한 파일인지 확인하고
     * 전체 경로를 반환한다 (태스크 0716).
     *
     * 경로 traversal(`/`, `..` 포함) 및 목록에 없는 파일명은 모두 null을
     * 반환한다 — `listBackups()`가 나열하는 화이트리스트에 속한 항목만
     * 통과시킨다.
     */
    public function resolveBackupPath(string $name): ?string
    {
        if ($name === '' || $name !== basename($name)) {
            return null;
        }

        if (!in_array($name, $this->listBackups(), true)) {
            return null;
        }

        return $this->backupDirectory . '/' . $name;
    }

    public function restoreBackup(array $uploadedFile): string
    {
        $this->ensureBackupDirectory();

        $name = is_string($uploadedFile['name'] ?? null) ? basename($uploadedFile['name']) : '';
        $tmpName = is_string($uploadedFile['tmp_name'] ?? null) ? $uploadedFile['tmp_name'] : '';
        $error = is_int($uploadedFile['error'] ?? null) ? $uploadedFile['error'] : UPLOAD_ERR_NO_FILE;

        if ($error !== UPLOAD_ERR_OK || $name === '' || $tmpName === '' || !is_file($tmpName)) {
            throw new \RuntimeException('복원할 백업 파일을 선택하세요.');
        }

        if (preg_match('/\.(json|sql)\z/i', $name) !== 1) {
            throw new \RuntimeException('복원 파일은 .json 또는 .sql이어야 합니다.');
        }

        $target = $this->backupDirectory . '/restore-upload-' . gmdate('Ymd-His') . '-' . $name;
        if (!@move_uploaded_file($tmpName, $target) && !@copy($tmpName, $target)) {
            throw new \RuntimeException('복원 파일을 저장할 수 없습니다.');
        }

        return basename($target);
    }

    private function ensureBackupDirectory(): void
    {
        if (!is_dir($this->backupDirectory) && !mkdir($this->backupDirectory, 0775, true)) {
            throw new \RuntimeException('백업 디렉터리를 만들 수 없습니다.');
        }
    }
}
