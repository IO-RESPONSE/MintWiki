# Config File Permission Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.
[Public Docroot Policy](public-docroot-policy.md)와 [PHP DB Configuration](php-db-config.md)을 기반으로,
웹호스팅 환경에서 민감한 설정 파일(config files)이 웹을 통해 직접 노출되지 않도록
파일 위치, 권한, 접근 제어를 정의한다.

## 목적

공용 웹호스팅에 배포할 때, 데이터베이스 자격증명, API 키, 환경 설정 등이 포함된
설정 파일이 웹 브라우저를 통해 접근되면 안 된다. 이 문서는 다음을 정의한다:

- **안전한 디렉토리 배치**: 설정 파일을 document root 외부에 배치하는 원칙
- **파일 권한 설정**: 웹 서버와 소유자만 읽을 수 있도록 제한하는 방식
- **접근 제어**: 웹 요청으로 설정 파일에 접근할 수 없는 메커니즘
- **검증 체크리스트**: 배포 전 권한 설정이 올바른지 검증하는 방법

## 적용 범위

- 공용 웹호스팅(cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 애플리케이션
- 데이터베이스 자격증명, API 키 등 민감한 정보가 포함된 설정 파일
- Apache 또는 Nginx를 사용하는 표준 웹 호스팅

적용되지 않는 것:

- 개발 환경 (로컬 개발자는 파일 권한을 느슨하게 설정할 수 있음)
- 설정이 모두 환경 변수로 제공되는 경우

## 1. 디렉토리 구조와 파일 배치

### 1.1 웹호스팅 배포 구조

호스팅에 배포될 때의 디렉토리 구조:

```
/home/user/                              ← 호스팅 계정 홈
├── public_html/                         ← 호스팅 제공자 기본 디렉토리
│   └── public/                          ← 웹 서버 document root (공개)
│       ├── index.php
│       └── assets/
├── config/                              ← 설정 파일 (비공개, 웹 접근 불가)
│   ├── database.php
│   ├── local-config.php
│   └── app.php
├── src/                                 ← 소스 코드 (비공개)
├── vendor/                              ← 의존성 (비공개)
└── storage/                             ← 런타임 파일 (비공개)
```

**핵심**: `config/` 디렉토리는 `/home/user/` 아래에 있으며, `/home/user/public_html/public/`
와 **형제 디렉토리**이다. 즉, document root(`public/`)에서 `../../../config/`를 통해서만 접근 가능하다.

### 1.2 application bootstrap에서 설정 파일 로드

PHP 애플리케이션은 상대 경로를 사용하여 document root 외부의 설정 파일을 로드한다:

```php
<?php
// public/index.php (front controller)
$projectRoot = dirname(__DIR__);  // /home/user/public_html 부모 = /home/user

// 설정 파일 로드 (document root 외부)
$configFile = $projectRoot . '/config/database.php';

if (!file_exists($configFile)) {
    die('설정 파일을 찾을 수 없습니다.');
}

$dbConfig = require $configFile;
```

이 방식으로:
- **웹 브라우저**: `GET /config/database.php` → 404 (document root 외부)
- **PHP 스크립트**: `require '../../../config/database.php'` → 로드 성공

## 2. 파일 권한 설정 (chmod)

### 2.1 최소 권한 원칙

설정 파일은 다음 원칙에 따라 권한을 설정한다:

- **소유자**: 읽기 필수 (배포, 유지보수 시 편집)
- **웹 서버**: 읽기 필수 (PHP가 파일을 로드)
- **그 외**: 접근 금지

### 2.2 권한 설정 방식

#### 옵션 A: 소유자만 접근 (더 엄격함)

```bash
chmod 600 /home/user/config/database.php
```

| 소유자 | 그룹 | 기타 |
|---|---|---|
| rw- (6) | --- (0) | --- (0) |

**사용 시기**:
- 호스팅 계정 소유자가 PHP를 실행하는 경우
- 웹 서버가 호스팅 계정 사용자로 실행되는 경우 (드물지만 일부 VPS)

#### 옵션 B: 웹 서버도 접근 (권장)

```bash
chmod 640 /home/user/config/database.php
chown user:www-data /home/user/config/database.php
```

| 소유자 | 그룹 | 기타 |
|---|---|---|
| rw- (6) | r-- (4) | --- (0) |

**사용 시기**:
- 표준 공용 호스팅 (cPanel, Plesk, DirectAdmin)
- 웹 서버가 `www-data`, `apache`, `nginx` 등의 별도 사용자로 실행
- **대부분의 호스팅이 이 방식을 권장**

**그룹 설정 확인**:

```bash
# 웹 서버 프로세스의 그룹 확인
ps aux | grep -E 'apache|nginx|www-data'

# 예: www-data 프로세스 실행 중
# www-data  1234  0.0  0.1  ... /usr/sbin/apache2

# 설정 파일의 현재 그룹 확인
ls -l /home/user/config/database.php
# -rw-r-----  1 user www-data  1024 Jul  3 15:47 database.php

# 그룹 변경 (필요시)
chown :www-data /home/user/config/database.php
```

### 2.3 디렉토리 권한

`config/` 디렉토리 자체도 보호해야 한다:

```bash
chmod 750 /home/user/config
```

| 소유자 | 그룹 | 기타 |
|---|---|---|
| rwx (7) | r-x (5) | --- (0) |

이렇게 설정하면:
- 소유자: 디렉토리 나열, 파일 읽기/쓰기 가능
- 웹 서버: 디렉토리 나열, 파일 읽기 가능
- 기타: 접근 불가

### 2.4 대량 권한 설정 스크립트

배포 시 한 번에 설정:

```bash
#!/bin/bash
# scripts/set-config-permissions.sh

PROJECT_ROOT="/home/user"
CONFIG_DIR="$PROJECT_ROOT/config"

# 디렉토리 권한
chmod 750 "$CONFIG_DIR"

# 모든 PHP 파일 권한
find "$CONFIG_DIR" -type f -name "*.php" -exec chmod 640 {} \;
find "$CONFIG_DIR" -type f -name "*.env*" -exec chmod 640 {} \;
find "$CONFIG_DIR" -type f -name "*.json" -exec chmod 640 {} \;

# 소유자 및 그룹 설정
chown -R user:www-data "$CONFIG_DIR"

echo "✓ Config file permissions set successfully"
```

실행:

```bash
bash scripts/set-config-permissions.sh
```

## 3. 웹 접근 제어 메커니즘

### 3.1 document root 외부 배치 (1차 방어)

설정 파일을 document root 외부에 배치하면, 웹 서버는 자동으로 이들 파일에 접근할 수 없다.

**웹 브라우저에서의 시도**:

```
GET https://example.com/config/database.php
     ↓
웹 서버: /home/user/public_html/public/config/database.php 찾기
     ↓
404 Not Found (파일이 document root 외부에 있음)
```

### 3.2 웹 서버 설정 (2차 방어, 옵션)

추가 보안을 위해, 호스팅사 패널이나 `.htaccess`에서 설정 파일 접근을 명시적으로 차단할 수 있다.

#### Apache (.htaccess)

```apache
# /home/user/public_html/.htaccess
<FilesMatch "\.php$|\.env|\.json">
    <IfModule mod_authz_core.c>
        Require all denied
    </IfModule>
    <IfModule !mod_authz_core.c>
        Order allow,deny
        Deny from all
    </IfModule>
</FilesMatch>
```

이 규칙은:
- document root(`public/`) 내의 `.php`, `.env`, `.json` 파일에 직접 접근 차단
- document root 외부 파일에는 영향 없음 (어차피 접근 불가)

#### Nginx

```nginx
# /etc/nginx/conf.d/example.com.conf
location ~ \.php$ {
    # PHP 파일 접근 제어
    # 단, document root 외부는 자동으로 차단됨
}

location ~ /\. {
    # 숨김 파일 및 디렉토리 차단
    deny all;
}
```

### 3.3 파일 시스템 권한 (3차 방어)

`chmod 640`으로 설정하면, 웹 서버 프로세스 외의 다른 사용자는 설정 파일을 읽을 수 없다.

```bash
# 호스팅 계정 A의 사용자가 호스팅 계정 B의 설정 파일 읽기 시도
cat /home/userB/config/database.php
# Permission denied (userA는 그룹에 포함되지 않음)
```

## 4. 호스팅별 설정 가이드

### 4.1 cPanel

**배포 단계**:

1. SSH 또는 호스팅 패널의 File Manager로 접속
2. 프로젝트를 `/home/user/public_html/` 아래에 배포 (또는 다른 디렉토리)
3. 실제 구조:
   ```
   /home/user/public_html/     ← 호스팅 루트
   ├── public/                 ← document root (웹 서버 설정에서 지정)
   ├── src/
   ├── vendor/
   └── config/                 ← 웹루트 밖
   ```

**권한 설정**:

```bash
ssh user@hosting.example.com

# 1. config/ 디렉토리 및 파일 권한 설정
chmod 750 ~/config
chmod 640 ~/config/*.php
chown -R user:www-data ~/config

# 2. 확인
ls -ld ~/config
# drwxr-x---  2 user www-data 4096 Jul  3 15:47 /home/user/config

ls -l ~/config/database.php
# -rw-r-----  1 user www-data 1024 Jul  3 15:47 /home/user/config/database.php
```

### 4.2 Plesk

**배포 단계**:

1. Domains → 도메인 선택 → File Manager
2. 프로젝트 배포 위치:
   ```
   /var/www/vhosts/example.com/
   ├── httpdocs/        ← document root (웹 서버 설정)
   ├── public/          ← 또는 여기 (구성에 따라 다름)
   └── config/          ← 웹루트 밖
   ```

**권한 설정** (SSH 접속 후):

```bash
# Plesk 환경에서 웹 서버 사용자는 보통 nobody
chmod 750 /var/www/vhosts/example.com/config
chmod 640 /var/www/vhosts/example.com/config/*.php
chown -R psacln:nobody /var/www/vhosts/example.com/config
```

### 4.3 DirectAdmin

**배포 단계**:

1. File Manager 또는 SSH 접속
2. 프로젝트 배포 위치:
   ```
   /home/user/public_html/
   ├── public/          ← document root
   └── config/          ← 웹루트 밖
   ```

**권한 설정**:

```bash
# DirectAdmin은 보통 apache 사용자
chmod 750 ~/config
chmod 640 ~/config/*.php
chown -R user:apache ~/config
```

### 4.4 자체 VPS/Dedicated 서버

**수동 배포**:

```bash
# 호스팅사 VPS 루트에서
mkdir -p /home/user/config

# 권한 설정
chmod 750 /home/user/config
chmod 640 /home/user/config/*.php

# 웹 서버 사용자에게 그룹 권한 부여
chown -R user:www-data /home/user/config
```

## 5. 설정 파일의 내용과 민감 정보

### 5.1 어떤 파일이 설정 파일인가?

다음 파일들은 민감한 정보를 포함하므로 document root 외부에 배치해야 한다:

| 파일명 | 내용 | 예 |
|---|---|---|
| `database.php` | DB 자격증명 | host, user, password |
| `local-config.php` | 호스팅별 설정 | API 키, 비밀번호 |
| `.env` | 환경 변수 | DB_PASSWORD, API_SECRET |
| `app.php` | 애플리케이션 설정 | 시크릿 키, 암호화 키 |
| `composer.json` | 의존성 정의 | 프로젝트 구조 노출 방지 |
| `composer.lock` | 의존성 버전 | 보안 취약점 탐색 대상 |

### 5.2 sample 파일 vs 실제 설정 파일

**sample 파일** (`database.php.sample`):

```php
<?php
return [
    'driver' => 'mysql',
    'dsn' => 'mysql:host=localhost;port=3306;dbname=wiki_engine',
    'user' => 'wiki_user',
    'password' => 'YOUR_PASSWORD_HERE',  // 플레이스홀더
];
```

**사항**:
- Repository에 커밋 가능
- 민감한 정보는 플레이스홀더
- 배포 시 실제 값으로 수정

**실제 설정 파일** (`database.php`):

```php
<?php
return [
    'driver' => 'mysql',
    'dsn' => 'mysql:host=db.example.com;port=3306;dbname=mysite_db',
    'user' => 'mysite_user',
    'password' => 'actual_secure_password_12345',  // 실제 비밀번호
];
```

**사항**:
- `.gitignore`에 추가 (커밋 금지)
- 배포 시만 생성
- 웹 접근 불가 (chmod 640, document root 외부)

## 6. 배포 체크리스트

배포 전 다음을 확인한다:

- [ ] 설정 파일이 document root 외부에 배치되었는가?
  ```bash
  ls -l ~/config/database.php
  # 파일이 /home/user/config/ 아래에 있어야 함
  ```

- [ ] 파일 권한이 올바르게 설정되었는가?
  ```bash
  ls -l ~/config/database.php
  # 예상: -rw-r----- (640) 또는 -rw------- (600)
  # 절대 금지: -rw-r--r-- (644) 또는 -rwxrwxrwx (777)
  ```

- [ ] 디렉토리 권한이 올바르게 설정되었는가?
  ```bash
  ls -ld ~/config
  # 예상: drwxr-x--- (750)
  ```

- [ ] 웹 브라우저에서 설정 파일에 접근할 수 없는가?
  ```bash
  # SSH 접속 후
  curl https://example.com/config/database.php
  # 예상: 404 Not Found
  
  curl https://example.com/../config/database.php
  # 예상: 404 Not Found
  ```

- [ ] PHP에서 설정 파일을 로드할 수 있는가?
  ```bash
  # 호스팅 패널의 PHP 테스트 또는 로그 확인
  # 설정 파일을 성공적으로 로드했는지 로그에서 확인
  ```

- [ ] 민감한 정보가 저장소에 커밋되지 않았는가?
  ```bash
  git log --all -- config/database.php config/.env
  # 어떤 커밋에도 이 파일들이 없어야 함
  
  git status
  # "nothing to commit" (설정 파일은 .gitignore 대상)
  ```

## 7. 테스트 및 검증

### 7.1 단위 테스트: 파일 배치 검증

```php
<?php
// php/tests/Config/FilePermissionTest.php
namespace MintWiki\Tests\Config;

use PHPUnit\Framework\TestCase;

final class FilePermissionTest extends TestCase
{
    private string $projectRoot;
    
    protected function setUp(): void
    {
        $this->projectRoot = dirname(__DIR__, 2);
    }
    
    /** @test */
    public function configDirectoryExistsOutsidePublic(): void
    {
        $configDir = dirname($this->projectRoot) . '/config';
        $publicDir = $this->projectRoot . '/public';
        
        // document root 외부에 있어야 함
        $this->assertDirectoryExists($configDir);
        $this->assertStringNotStartsWith(
            $publicDir,
            $configDir,
            'config/ must not be inside public/'
        );
    }
    
    /** @test */
    public function configDatabasePhpExists(): void
    {
        $configFile = dirname($this->projectRoot) . '/config/database.php';
        // .sample 또는 실제 파일 중 하나는 있어야 함
        $this->assertTrue(
            file_exists($configFile) || file_exists($configFile . '.sample'),
            'database.php or database.php.sample must exist'
        );
    }
    
    /** @test */
    public function sampleFilesAreInRepository(): void
    {
        // sample 파일들은 저장소에 있어야 함
        $samples = [
            dirname($this->projectRoot) . '/config/database.php.sample',
        ];
        
        foreach ($samples as $file) {
            $this->assertFileExists($file, "Sample file must exist: $file");
        }
    }
}
```

### 7.2 통합 테스트: 웹 접근 불가 검증

```php
<?php
// php/tests/Integration/ConfigWebAccessTest.php
namespace MintWiki\Tests\Integration;

use PHPUnit\Framework\TestCase;

final class ConfigWebAccessTest extends TestCase
{
    private string $baseUrl = 'http://localhost:8000';
    
    /** @test */
    public function cannotAccessConfigDatabase(): void
    {
        $response = $this->getHttp('/config/database.php');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessConfigDirectory(): void
    {
        $response = $this->getHttp('/config/');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessDotEnv(): void
    {
        $response = $this->getHttp('/.env');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessComposerJson(): void
    {
        $response = $this->getHttp('/composer.json');
        $this->assertEquals(404, $response['status']);
    }
    
    private function getHttp(string $path): array
    {
        $url = $this->baseUrl . $path;
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        
        curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return ['status' => (int)$status];
    }
}
```

### 7.3 배포 검증 스크립트

```bash
#!/bin/bash
# scripts/verify-config-permissions.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="$(dirname "$PROJECT_ROOT")/config"
PUBLIC_DIR="$PROJECT_ROOT/public"

echo "Config Permission Verification"
echo "=============================="

# 1. config/ 디렉토리 존재 확인
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ config/ directory not found at $CONFIG_DIR"
    exit 1
fi
echo "✓ config/ directory exists"

# 2. config/가 public/ 외부에 있는지 확인
if [[ "$CONFIG_DIR" == "$PUBLIC_DIR"* ]]; then
    echo "❌ config/ is inside public/ (security risk)"
    exit 1
fi
echo "✓ config/ is outside public/"

# 3. 민감한 파일 권한 확인
for file in database.php local-config.php app.php .env; do
    path="$CONFIG_DIR/$file"
    
    if [ -f "$path" ]; then
        perms=$(stat -c '%a' "$path" 2>/dev/null || stat -f '%OLp' "$path" | sed 's/.*\(..\)$/\1/')
        
        # 600 또는 640만 허용
        if [[ "$perms" != "600" && "$perms" != "640" ]]; then
            echo "❌ File has insecure permissions: $file ($perms)"
            echo "   Expected: 600 or 640"
            exit 1
        fi
        echo "✓ $file has secure permissions ($perms)"
    fi
done

# 4. 디렉토리 권한 확인
dir_perms=$(stat -c '%a' "$CONFIG_DIR" 2>/dev/null || stat -f '%OLp' "$CONFIG_DIR" | sed 's/.*\(..\)$/\1/')
if [[ "$dir_perms" != "750" ]]; then
    echo "⚠ config/ directory permissions might not be restrictive enough ($dir_perms)"
    echo "  Recommended: 750"
fi

echo ""
echo "✅ All config permission checks passed"
exit 0
```

실행:

```bash
bash scripts/verify-config-permissions.sh
```

## 8. 보안 고려사항

### 8.1 파일 권한만으로는 부족

파일 권한(`chmod`)은 **파일 시스템 수준**의 접근 제어이며, 다음 위협으로부터는 방어하지 않는다:

- **웹 서버 프로세스 권한 상승**: 웹 서버가 권한 상승(privilege escalation) 취약점으로 root가 된다면, `chmod 640`도 우회 가능
- **다른 호스팅 계정의 접근**: 공유 호스팅에서 같은 머신의 다른 계정은 같은 권한 수준일 수 있음
- **백업 파일**: 백업이 웹에 노출될 수 있음

**추가 방어**:
- document root 외부 배치 (이 정책의 핵심)
- 호스팅사의 계정 격리 확인
- 백업 파일의 권한 설정
- 정기적인 보안 감사

### 8.2 실수로 인한 설정 파일 노출

배포 시 다음 실수가 발생할 수 있다:

| 실수 | 결과 | 방지 방법 |
|---|---|---|
| 설정 파일을 `public/` 안에 배치 | 웹 노출 | 배포 스크립트에서 검증 |
| 권한을 `644` 또는 `777`로 설정 | 다른 사용자도 읽기 가능 | 배포 후 `verify-config-permissions.sh` 실행 |
| 설정 파일을 repository에 커밋 | 버전 관리에 민감 정보 노출 | `.gitignore`에 추가하고 pre-commit hook으로 검증 |
| 호스팅 패널의 "Public HTML" 폴더에만 배포 | 기본값이 웹 노출 | 호스팅사에 다른 디렉토리 생성 권한 요청 |

## 9. 일반적인 문제 해결

### 9.1 "Permission denied" 오류

**증상**: PHP에서 `require '/home/user/config/database.php'` 시 permission denied

**원인**:
- 파일 권한이 너무 제한적 (소유자만 600)
- 웹 서버 사용자가 그룹에 포함되지 않음
- 파일 소유자가 호스팅 계정 사용자가 아님

**해결**:

```bash
# 1. 현재 파일 및 그룹 확인
ls -l ~/config/database.php
# -rw------- 1 user user 1024 ...  ← 웹 서버가 그룹에 없음

# 2. 웹 서버 사용자 확인
ps aux | grep -E 'apache|nginx|www-data' | head -1

# 3. 권한 및 그룹 수정
chmod 640 ~/config/database.php
chown user:www-data ~/config/database.php

# 4. 재확인
ls -l ~/config/database.php
# -rw-r----- 1 user www-data 1024 ...
```

### 9.2 호스팅사가 config 디렉토리 생성을 허용하지 않음

**증상**: 호스팅 패널의 File Manager에서 `/home/user/` 아래에 새 폴더를 만들 수 없음

**원인**: 일부 호스팅사는 `public_html/` 폴더 내에만 파일 관리를 허용

**해결책**:

**옵션 A: 호스팅사 지원 요청** (권장)
- "Public HTML 외부에 `config/` 폴더를 만들 수 있게 해달라"고 요청
- 대부분의 호스팅사가 수용

**옵션 B: SSH로 수동 생성**

```bash
ssh user@hosting.example.com
mkdir -p ~/config
chmod 750 ~/config
```

**옵션 C: 설정 파일을 public 내 숨김 디렉토리에 배치** (비권장)

```
/home/user/public_html/
├── public/
│   └── .config/           ← 점으로 시작하면 일반적으로 숨김
│       └── database.php
└── index.php
```

**단점**:
- 여전히 document root 내부 (설정 오류 시 노출 위험)
- 웹 서버 설정으로 추가 차단 필요
- `.gitignore`에서 `.config/`를 명확히 지정해야 함

### 9.3 개발 환경에서는 권한 설정이 필요한가?

**개발 환경**: 로컬 머신에서 코드를 작성하고 테스트

- 권한 설정 생략 가능 (모든 사용자가 권한 있음)
- 단, PHP가 파일을 읽을 수 있으면 됨
- 배포 전에만 호스팅 환경에 맞춘 권한 설정

**테스트 환경**: CI/CD 파이프라인에서 실행

- 배포 환경과 유사하게 권한 설정 (선택사항)
- `verify-config-permissions.sh`는 실행해서 배포 전 검증

## 10. 관련 문서

- [Public Docroot Policy](public-docroot-policy.md) — document root 구조와 파일 배치
- [PHP DB Configuration](php-db-config.md) — 설정 파일 형식과 로드 방식
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — 호스팅 환경 요구사항

## 후속 태스크 연결

- **0615**: Web config sample (호스팅별 설정 파일 샘플)
- **0616**: Local config loader (설정 파일 로드 메커니즘)
- **0618+**: Installer 스크립트 (배포 시 권한 자동 설정)
