# php/src/Modules

모듈별 PHP 포팅 코드가 들어갈 namespace 골격. 각 하위 디렉터리는
`docs/php-namespace-mapping.md` 가 고정한 `MintWiki\<Module>` namespace 에
대응하며, 태스크 0399 시점에는 비어 있다(README만 존재) — 실제 클래스는
각 모듈의 포팅이 시작되는 이후 Phase B/C 태스크에서 채워진다.

| 디렉터리 | namespace | Python 원본 패키지 |
|---|---|---|
| `Document/` | `MintWiki\Document` | `modules.document` |
| `Revision/` | `MintWiki\Revision` | `modules.revision` |
| `Parser/` | `MintWiki\Parser` | `modules.parser` |
| `Render/` | `MintWiki\Render` | `modules.render` |
| `Acl/` | `MintWiki\Acl` | `modules.acl` |
| `Discussion/` | `MintWiki\Discussion` | `modules.discussion` |
| `Search/` | `MintWiki\Search` | `modules.search` |
| `Cache/` | `MintWiki\Cache` | `modules.cache` |
| `Jobs/` | `MintWiki\Jobs` | `modules.jobs` |
| `User/` | `MintWiki\User` | `modules.user` |
| `Admin/` | `MintWiki\Admin` | `modules.admin` |
| `Audit/` | `MintWiki\Audit` | `modules.audit` |

이 표는 `docs/php-namespace-mapping.md` 의 모듈별 매핑 표를 그대로
옮긴 것이다 — 값이 어긋나면 그 문서를 기준으로 이 표를 고친다.
