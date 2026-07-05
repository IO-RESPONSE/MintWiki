/**
 * 편집 툴바 점진적 향상 스크립트 (태스크 0709).
 *
 * 기본 동작(JS 없이도 편집·저장은 정상)은 `DocumentEditorPage`의 툴바 버튼이
 * 전부 `type="button"`이라 아무 폼도 제출하지 않는 무동작 버튼인 것이다 —
 * 사용자가 문법을 직접 타이핑하면 된다. 이 스크립트가 로드되면 각 버튼의
 * `data-markup-before`/`data-markup-after` 속성값으로 textarea#source의
 * 선택 영역을 감싸거나(선택 영역이 있으면) 삽입한다(선택 영역이 없으면 커서
 * 위치에 두 값을 이어붙이고 그 사이에 커서를 남긴다).
 *
 * 외부 의존성 없음.
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

    function applyMarkup(textarea, before, after) {
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var value = textarea.value;
        var selected = value.slice(start, end);

        textarea.value = value.slice(0, start) + before + selected + after + value.slice(end);

        var cursorStart = start + before.length;
        var cursorEnd = cursorStart + selected.length;
        textarea.focus();
        textarea.setSelectionRange(cursorStart, cursorEnd);
    }

    onReady(function () {
        var textarea = document.getElementById('source');
        var buttons = document.querySelectorAll('.editor-toolbar__button');

        if (!textarea || buttons.length === 0) {
            return;
        }

        buttons.forEach(function (button) {
            button.addEventListener('click', function () {
                var before = button.getAttribute('data-markup-before') || '';
                var after = button.getAttribute('data-markup-after') || '';
                applyMarkup(textarea, before, after);
            });
        });
    });
})();
