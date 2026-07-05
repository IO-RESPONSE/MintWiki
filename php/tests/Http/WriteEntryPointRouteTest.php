<?php

declare(strict_types=1);

/**
 * `GET /write` 새 문서 작성 진입점과 상단 네비게이션 링크를 확인한다 (태스크 0703).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\NavigationItem;

$failures = [];

$router = new Router();
$router->register('GET', '/write', static function (): Response {
    $navigation = new Navigation([
        new NavigationItem('/write', '글쓰기', '/write'),
    ]);
    $headerContent = (new NavigationBar())->render($navigation, '/write', []);
    $layout = new Layout(null, $headerContent);
    $documentEditorPage = new DocumentEditorPage(null, $layout);

    return Response::html($documentEditorPage->render('__new__', '', '', true));
});

$handler = $router->match(new Request('GET', '/write'));

if ($handler === null) {
    $failures[] = 'GET /write route는 등록되어 있어야 한다.';
} else {
    $response = $handler();

    if ($response->status() !== 200) {
        $failures[] = 'GET /write 응답은 200이어야 한다.';
    }

    $body = $response->body();

    if (!str_contains($body, '<h1>새 문서 만들기</h1>')) {
        $failures[] = 'GET /write는 새 문서 작성 폼을 렌더링해야 한다.';
    }

    if (!str_contains($body, '<input type="text" id="title" name="title" value="" required>')) {
        $failures[] = 'GET /write는 비어 있는 제목 입력 필드를 보여줘야 한다.';
    }

    if (!str_contains($body, '<textarea id="source" name="source" required></textarea>')) {
        $failures[] = 'GET /write는 비어 있는 본문 입력 필드를 보여줘야 한다.';
    }

    if (!str_contains($body, 'action="/wiki/__new__/edit"')) {
        $failures[] = 'GET /write form은 기존 /wiki/{title}/edit 저장 경로를 재사용해야 한다.';
    }

    if (!str_contains($body, '<a class="site-nav__link site-nav__link--active" href="/write" aria-current="page">글쓰기</a>')) {
        $failures[] = '상단 네비게이션의 글쓰기 링크가 /write로 노출되고 활성화되어야 한다.';
    }
}

if ($router->match(new Request('POST', '/write')) !== null) {
    $failures[] = 'POST /write는 등록하지 않고 기존 /wiki/{title}/edit POST 흐름을 사용해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "GET /write 작성 진입점 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /write 작성 진입점 테스트 통과.\n");
exit(0);
