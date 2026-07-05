<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 유지보수 모드 상태를 DB보다 먼저 읽을 수 있는 작은 PHP 설정 파일에 저장한다.
 */
final class MaintenanceModeStateStore
{
    public function __construct(private readonly string $filePath)
    {
    }

    public static function atDefaultPath(): self
    {
        return new self(dirname(__DIR__, 2) . '/config/maintenance-mode.php');
    }

    public function isEnabled(): bool
    {
        if (!is_file($this->filePath) || !is_readable($this->filePath)) {
            return false;
        }

        $config = @include $this->filePath;
        if (!is_array($config)) {
            return false;
        }

        return ($config['enabled'] ?? false) === true;
    }

    public function setEnabled(bool $enabled): void
    {
        $directory = dirname($this->filePath);
        if (!is_dir($directory) && !mkdir($directory, 0775, true)) {
            throw new \RuntimeException('유지보수 설정 디렉터리를 만들 수 없습니다.');
        }

        $contents = "<?php\n\nreturn [\n    'enabled' => " . ($enabled ? 'true' : 'false') . ",\n];\n";
        if (file_put_contents($this->filePath, $contents, LOCK_EX) === false) {
            throw new \RuntimeException('유지보수 설정을 저장할 수 없습니다.');
        }
    }
}
