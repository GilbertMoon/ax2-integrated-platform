"""과제 설명(리치텍스트) HTML 정제 — 저장 시(tutor.forms)와 렌더링 시(템플릿 필터) 공용.

렌더링 시에도 다시 한 번 정제하는 이유: 이 기능이 생기기 전에 plain text 로 저장된
기존 Assignment.description 값이나, 폼을 거치지 않고 DB에 직접 들어간 값은
허용되지 않은 태그를 담고 있을 수 있다. `|safe` 로 그대로 내보내면 위험하므로
템플릿에서도 항상 이 정제를 한 번 더 거친다.

허용 태그는 Trix 에디터(과제 설명 입력에 쓰는 리치텍스트 에디터)가 실제로 내보내는
태그 기준이다 — 특히 "div" 는 Trix 가 문단마다 기본으로 감싸는 태그라서 빼면 안 된다
(문단 구분이 통째로 사라짐). blockquote/h1/pre/del 은 툴바에는 없지만 다른 곳에서
복사·붙여넣기한 서식을 Trix 가 인식했을 때 나올 수 있어 같이 허용한다.
Trix 는 이미지를 <figure data-trix-attachment="..."><img ...></figure> 로 감싸
내보내는데, figure/데이터 속성은 허용 목록에 없어 정제 시 벗겨지고 안의 <img> 만
남는다 — 의도된 동작이다 (다시 Trix 에 불러와도 img 는 새 첨부로 인식된다).
"""

import bleach

ASSIGNMENT_DESCRIPTION_ALLOWED_TAGS = [
    "b", "strong", "i", "em", "u", "del",
    "div", "p", "br", "span",
    "h1", "blockquote", "pre",
    "ul", "ol", "li", "a", "img",
]
ASSIGNMENT_DESCRIPTION_ALLOWED_ATTRS = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt"],
}


def clean_assignment_description(raw: str) -> str:
    return bleach.clean(
        raw or "",
        tags=ASSIGNMENT_DESCRIPTION_ALLOWED_TAGS,
        attributes=ASSIGNMENT_DESCRIPTION_ALLOWED_ATTRS,
        strip=True,
    )
