/**
 * 편집 화면 미리보기 점진적 향상 스크립트 (태스크 0708).
 *
 * 기본 동작(JS 없이도 동작)은 `DocumentEditorPage`의 "미리보기" 버튼이
 * `formaction`으로 가리키는 `POST /wiki/{title}/preview`로 브라우저가 그대로
 * 이동하는 것이다 — 서버가 같은 편집 화면을 다시 렌더링해 미리보기 영역을
 * 채워 돌려준다. 이 스크립트는 그 이동을 fetch로 가로채 페이지 전체를
 * 새로고침하지 않고 미리보기 영역만 갱신한다. CSRF 토큰은 매 검증마다
 * 소모되므로, 응답에 담긴 새 토큰으로 폼의 hidden input을 갱신해야 다음
 * "저장"/"미리보기" 제출이 계속 유효하다.
 *
 * 외부 의존성 없음. fetch 실패 등 어떤 이유로든 이 스크립트가 동작하지
 * 않아도 버튼은 formaction/formmethod만으로 여전히 정상 동작한다.
 */
(function () {
    'use strict';

    function onReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }

    onReady(function () {
        var form = document.querySelector('.document-editor-form');
        var previewButton = form ? form.querySelector('.document-editor-preview-button') : null;
        var previewContent = document.getElementById('edit-preview-content');

        if (!form || !previewButton || !previewContent || typeof window.fetch !== 'function') {
            return;
        }

        previewButton.addEventListener('click', function (event) {
            event.preventDefault();

            var formData = new FormData(form);

            fetch(previewButton.getAttribute('formaction'), {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
                .then(function (response) {
                    return response.text();
                })
                .then(function (html) {
                    var parsedDocument = new DOMParser().parseFromString(html, 'text/html');
                    var newPreviewContent = parsedDocument.getElementById('edit-preview-content');
                    var newCsrfInput = parsedDocument.querySelector('input[name="csrf_token"]');
                    var csrfInput = form.querySelector('input[name="csrf_token"]');

                    if (newPreviewContent) {
                        previewContent.innerHTML = newPreviewContent.innerHTML;
                    }
                    if (newCsrfInput && csrfInput) {
                        csrfInput.value = newCsrfInput.value;
                    }
                })
                .catch(function () {
                    // 네트워크 오류 시에는 미리보기만 갱신되지 않을 뿐, 편집/저장은
                    // 계속 정상 동작한다(진행 중인 입력을 건드리지 않는다).
                });
        });
    });
})();
