<?php

declare(strict_types=1);

namespace MintWiki\Admin;

interface BackupRunner
{
    /**
     * @return string 생성된 백업 이름
     */
    public function createBackup(): string;

    /**
     * @return string[]
     */
    public function listBackups(): array;

    /**
     * @param array<string, mixed> $uploadedFile
     */
    public function restoreBackup(array $uploadedFile): string;
}
