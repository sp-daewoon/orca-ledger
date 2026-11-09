# orca-ledger (한국어)

[Orca](https://github.com/stablyai/orca)에서 코딩 에이전트를 여러 개 돌릴 때 쓰는 **기록 층**입니다.

지휘는 하지 않습니다. Orca가 이미 하고, 그 위에 올라간 좋은 프로젝트도 여럿 있습니다. 이건 그들이 빼놓은 쪽입니다 — 만들어진 worktree·브랜치·run·작업자를 대장에 남기고 실제로 살아 있는 것과 대조하는 일, 그리고 지도의 사실이 조용히 낡지 않게 하는 일입니다.

에이전트를 저장소보다 **한 단계 위**에서 시작시킵니다. 그 위치에 마크다운 git 저장소 하나를 두고, 에이전트가 코드를 건드리기 전에 시스템 구조, 이미 내린 결정, 살아 있는 worktree, 자기가 해도 되는 일의 경계를 먼저 알게 합니다.

바이너리도 데몬도 가입도 없습니다. 마크다운, 스킬 3개, 표준 라이브러리만 쓰는 파이썬 스크립트 하나입니다.

```bash
npx skills add sp-daewoon/orca-ledger --agent claude-code
```

설치 후 에이전트에게 **"orca-ledger 워크스페이스 만들어줘"**라고 하면 됩니다.

## 이름에 대해

ledger는 항목을 적어 넣고 실제와 맞춰 보는 장부입니다. 이 도구가 하는 일이 그것뿐이라 그대로 이름으로 썼습니다.

`orca-` 접두어는 이게 Orca에서만 동작하기 때문입니다. 아래 대조 기능은 Orca가 worktree·dispatch·작업자 상태를 `--json`으로 내주기 때문에만 가능하고, 다른 것을 가리키면 마크다운 관례와 에러로 끝나는 스크립트만 남습니다. `orca-` 접두어는 Orca 자체 스킬의 작명(`orca-cli`, `orca-linear`, `orca-per-workspace-env`)에 맞춘 것이고, 그래야 이게 필요한 사람이 찾습니다.

비공식이며 Stably 및 Orca 프로젝트와 관련이 없습니다. Orca 메인테이너가 다른 이름을 원하면 이슈를 열면 바꿉니다.

## 문서는 영문, 답변은 한국어

하네스 파일(`AGENTS.md`, 플레이북)은 영문 한 벌만 유지합니다. 번역본을 두면 둘 중 하나는 반드시 낡기 때문입니다.

대신 설치할 때 에이전트가 **사용자가 쓰는 언어를 감지해** 응대 언어로 기록합니다. 한국어로 말을 걸었으면 `Answer in Korean, and always use formal speech (존댓말)`가 계약서에 박히고, 그 뒤로는 진행 보고와 최종 답변 모두 한국어 존댓말로 옵니다. 계약서는 에이전트가 읽는 문서라 영문이어도 동작에 차이가 없습니다.

## 푸는 문제 세 가지

에이전트 하나 돌릴 때는 아무 문제가 없습니다. 여러 저장소에 여러 개를 돌릴 때 무너집니다.

**1. 자원이 샙니다.** 작업자를 띄우고, 결과를 받고, 넘어갑니다. 사흘 뒤에 worktree가 아홉 개 있고, Orca는 작업자 둘을 아직 살아 있다고 보고 있고, 어딘가 잊은 worktree가 브랜치를 잡고 있어서 그 브랜치를 어디서도 체크아웃할 수 없습니다.

orca-ledger는 worktree, 브랜치, 작업자, dispatch를 전부 대장에 적습니다. **자원을 만들기 전에** 적기 때문에, 생성이 실패해도 고아를 찾을 단서가 남습니다. 그리고 대장을 실제 상태와 대조합니다.

```
$ python3 scripts/ledger-status.py
[unlisted worktrees]
  /Users/me/orca/workspaces/api/spike-3 (spike-3)
[ledger mismatch]
  payments-retry /Users/me/wt/api-retry: ledger a1b2c3d, actual 9f8e7d6
[unreleased workers]
  payments-retry dsp_4e2a reclaimable user_takeover: /Users/me/wt/api-retry
```

조회만 합니다. 아무것도 지우지 않습니다.

**2. 사실이 썩습니다.** 에이전트가 6주 전 메모를 읽고 현재 사실로 말합니다. 그래서 모든 사실에 세 가지를 붙이고, `confirmed`가 아니면 주장하지 못하게 계약에 박았습니다.

```yaml
- from: checkout-api
  to: pricing-engine
  type: http
  summary: 장바구니 렌더링 시 가격 조회
  status: confirmed        # confirmed | assumed | historical
  evidence:
    - checkout-api/src/main/java/.../PricingClient.java:42
  checked_at: 2026-11-09
```

`confirmed`가 아닌 항목은 답하기 전에 코드에서 다시 읽어야 합니다. 이게 전부이고, YAML 세 줄입니다.

**3. "완료"는 완료가 아닙니다.** 작업자의 성공 보고는 검증이 아닙니다. 두 작업자가 같은 답을 내도 검증이 아닙니다 — 같은 전제를 공유하니까요. orca-ledger는 메인 세션이 코드와 테스트로 확인한 뒤, 결과를 **커밋하지 않은 상태로** 사용자 체크아웃에 올립니다. 사용자가 자기 에디터에서 diff를 보고 직접 커밋합니다. 에이전트는 사용자 브랜치에 커밋하지 않습니다.

## 설계 근거

왜 이렇게 생겼는지, 무엇을 시도하고 버렸는지는 [docs/why.md](../why.md)에 있습니다(영문). 요약하면:

- **마크다운이지 서비스가 아닙니다.** 이 저장소의 내용이 곧 에이전트의 지시문이라, 도구 없이 사람이 읽고 고치고 리뷰에서 diff로 볼 수 있어야 했습니다. DB를 쓰면 대장 조회는 쉬워지고 계약서 리뷰는 불가능해집니다.
- **신뢰도 점수 대신 세 필드.** 모델이 내놓는 confidence 숫자는 안정적인 의미가 없습니다. `confirmed`는 "코드에서 읽었고 파일과 줄이 여기다"라는 검증 가능한 정의가 있습니다.
- **대조는 읽기만 합니다.** 자동 정리는 거부했습니다. 사용자가 직접 만든 worktree와 에이전트가 버린 고아를 구별할 단서가 대장뿐인데, 불일치가 났다는 건 바로 그 대장이 못 믿을 상태라는 뜻입니다.
- **Orca 전용입니다.** 고아 탐지가 이 프로젝트의 핵심이고, 그건 Orca가 dispatch와 작업자 상태를 `--json`으로 내주기 때문에 가능합니다. "아무 오케스트레이터나"로 추상화하면 그 기능이 `git worktree list` 수준으로 내려갑니다.

## 이건 무엇이 아닌가

Orca 위에서 worker를 보내고 결정 게이트를 두고 멀티 에이전트를 지휘하는 프로젝트가 이미 여럿 있습니다 — [dely](https://github.com/hieuphung97/dely), [orca-sdlc-kit](https://github.com/vankhangfet/orca-sdlc-kit), [mogui-ADE-orchestrator](https://github.com/baksohyeon/mogui-ADE-orchestrator) 등입니다. 지휘자가 필요하면 그쪽을 쓰십시오. 괜찮은 것들이 있습니다.

이건 나머지 절반입니다. 그중 무엇도 만들어진 자원을 지속적으로 기록하거나, 살아 있는 것과 대조하거나, 사실에 유효기간을 두지 않습니다. 쓰시는 지휘자 옆에 같이 두고 쓰는 물건입니다.

## 아직 못 푼 것

- 한 대장에 여러 세션이 동시에 쓰는 문제는 관례로만 막고 있습니다(대장 하나에 주인 하나).
- `checked_at`은 확인 시점을 적지만, 8개월 된 `confirmed`를 자동으로 의심하지는 않습니다.
- 지도는 작업한 만큼만 찹니다. 초기에는 "아직 안 봄"이 정직한 답이고, 그래서 처음 몇 주는 비어 보입니다. 추측으로 채우는 쪽을 버린 결과입니다.
- 저자 한 사람의 작업 방식에서 나왔습니다. 몇 가지는 원칙의 옷을 입은 개인 습관일 겁니다. 안 맞는 지점을 적은 이슈가 패치보다 유용합니다.

## 라이선스

MIT
