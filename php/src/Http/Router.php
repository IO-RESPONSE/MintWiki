<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * 정적 route만 매칭하는 라우터 골격 (태스크 0397).
 *
 * method + path 문자열이 완전히 일치하는 경우에만 매칭한다 — 동적
 * 세그먼트(`/articles/{id}` 등)나 와일드카드는 지원하지 않는다. route
 * 등록 자체를 검증하는 테스트(0398)와 실제 핸들러 실행/front controller
 * 연결(0419 health endpoint 등)은 이후 태스크에서 이어진다.
 */
final class Router
{
    /**
     * @var array<string, array<string, callable>>
     */
    private array $routes = [];

    public function register(string $method, string $path, callable $handler): void
    {
        $this->routes[strtoupper($method)][$path] = $handler;
    }

    /**
     * 요청의 method와 path에 정확히 일치하는 핸들러를 반환한다.
     * 일치하는 route가 없으면 null을 반환한다.
     */
    public function match(Request $request): ?callable
    {
        $method = strtoupper($request->method());
        $path = $request->path();

        return $this->routes[$method][$path] ?? null;
    }
}
