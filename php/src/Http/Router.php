<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * 정적 route와 `{name}` 동적 세그먼트를 함께 지원하는 라우터 (태스크 0397, 0675).
 *
 * method + path 문자열이 완전히 일치하는 정적 route를 항상 먼저 확인하고,
 * 일치하는 정적 route가 없을 때만 `/wiki/{title}` 같은 동적 세그먼트
 * route를 순서대로 검사한다 — 정적 route가 동적 route보다 우선한다.
 * 매칭된 동적 세그먼트 값은 `array<string, string>` 형태로 핸들러의
 * 첫 번째 인자로 전달된다. 정적 route 핸들러는 기존과 동일하게 인자 없이
 * 호출해도 그대로 동작한다(하위 호환). 정규식 제약, optional 세그먼트 등
 * 고급 기능은 이후 태스크에서 다룬다.
 */
final class Router
{
    /**
     * @var array<string, array<string, callable>>
     */
    private array $routes = [];

    /**
     * @var array<string, array<string, callable>>
     */
    private array $dynamicRoutes = [];

    public function register(string $method, string $path, callable $handler): void
    {
        $method = strtoupper($method);

        $this->routes[$method][$path] = $handler;

        if (str_contains($path, '{')) {
            $this->dynamicRoutes[$method][$path] = $handler;
        }
    }

    /**
     * 요청의 method와 path에 일치하는 핸들러를 반환한다. 정적 route를 먼저
     * 확인하고, 없으면 동적 세그먼트 route를 등록 순서대로 검사한다.
     * 일치하는 route가 없으면 null을 반환한다.
     */
    public function match(Request $request): ?callable
    {
        $method = strtoupper($request->method());
        $path = $request->path();

        if (isset($this->routes[$method][$path])) {
            return $this->routes[$method][$path];
        }

        foreach ($this->dynamicRoutes[$method] ?? [] as $registeredPath => $handler) {
            $params = self::matchSegments($registeredPath, $path);

            if ($params !== null) {
                return static fn () => $handler($params);
            }
        }

        return null;
    }

    /**
     * 등록된 path 템플릿과 실제 요청 path를 세그먼트 단위로 비교한다.
     * 일치하면 `{name}` 세그먼트 값을 담은 배열을, 일치하지 않으면 null을
     * 반환한다.
     *
     * @return array<string, string>|null
     */
    private static function matchSegments(string $registeredPath, string $requestPath): ?array
    {
        $registeredSegments = explode('/', trim($registeredPath, '/'));
        $requestSegments = explode('/', trim($requestPath, '/'));

        if (count($registeredSegments) !== count($requestSegments)) {
            return null;
        }

        $params = [];

        foreach ($registeredSegments as $index => $segment) {
            $requestSegment = $requestSegments[$index];

            if (preg_match('/^\{(.+)\}$/', $segment, $matches) === 1) {
                $params[$matches[1]] = $requestSegment;
                continue;
            }

            if ($segment !== $requestSegment) {
                return null;
            }
        }

        return $params;
    }
}
