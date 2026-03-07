# kakaocli RAG Blocker Report

Date: 2026-03-07
Workspace: `/Users/alice/Documents/codex`
Goal: determine whether KakaoTalk chat-conversation RAG is currently possible on this Mac using `kakaocli`

## Verdict

Current RAG status: **NO**

Reason:
- KakaoTalk UI is accessible and appears logged in.
- `kakaocli` is installed and runnable.
- But `kakaocli` cannot open the local encrypted message database, because `auth` cannot discover the Kakao `userId`.
- Without successful `auth`, the read path required for RAG (`chats`, `messages`, `search`, `query`) is not available.

## Environment

- macOS with full Xcode installed and selected
- `xcode-select -p`:
  - `/Applications/Xcode.app/Contents/Developer`
- `xcodebuild -version`:
  - `Xcode 26.3`
  - `Build version 17C529`
- `kakaocli` installation:
  - `command -v kakaocli` => `/opt/homebrew/bin/kakaocli`
  - `brew list --versions kakaocli` => `kakaocli 0.5.0`

## What Works

### 1. KakaoTalk UI is visible and readable through Accessibility

`kakaocli inspect --depth 2` succeeded and returned the main KakaoTalk window tree.

Observed structure included:
- main window title `KakaoTalk`
- `chatrooms` tab/button
- chat list scroll area and table

This means:
- KakaoTalk is running
- Accessibility access is likely working
- The chat list is visible to UI automation

### 2. The chat list is populated

A read-only AX script enumerated visible rows and returned:

```text
ROW_COUNT=828
1   self=false  name=정체성 없는 언정인들
2   self=false  name=[코드팩토리] 바이브코딩 x 클로드 코드
3   self=false  name=이스타항공
...
14  self=true   name=조민석
...
```

This means:
- the account is not in a fresh logged-out state
- the main chat list is real and populated
- self-chat is visible in the UI

### 3. KakaoTalk preferences contain account-like data

`defaults read com.kakao.KakaoTalkMac` and the container plist show data such as:

- `Email = "cho9911@gmail.com"`
- `AlertKakaoIDsList = [25411718, 344940307, 388584983, 366369712]`

This suggests KakaoTalk account state exists locally.

## What Fails

### 1. `kakaocli auth` fails immediately

Command:

```bash
kakaocli auth
```

Observed output:

```text
UUID: 2B869014-C939-599E-BF18-50C2865BB565
Error: Could not find user ID in plist. Available keys: Could not extract from FSChatWindowTransparency keys or direct lookup

Could not auto-detect user ID.
Try: kakaocli auth --user-id <YOUR_KAKAO_USER_ID>

To find your user ID, check:
  defaults read com.kakao.KakaoTalkMac
```

This is the primary blocker.

### 2. Candidate numeric IDs from plist did not work

Tested:

```bash
kakaocli auth --user-id 25411718
kakaocli auth --user-id 344940307
kakaocli auth --user-id 388584983
kakaocli auth --user-id 366369712
```

All failed with the same pattern:
- `kakaocli` derived a database filename
- that filename did not exist in the KakaoTalk container

Example failure shape:

```text
UUID: 2B869014-C939-599E-BF18-50C2865BB565
User ID: <candidate>
Database NOT found at: /Users/alice/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Application Support/com.kakao.KakaoTalkMac/<derived-name>[.db]
```

Conclusion:
- the plist numeric candidates are not enough by themselves
- they are not the actual current account `userId`, or not the one required for DB derivation

### 3. `status` and `login --status` are unstable

Observed behavior:
- `kakaocli status` succeeded once and reported:
  - `App installed: Yes`
  - `Container exists: Yes`
  - `Preferences exist: No`
  - `Database files: 0`
  - `Full Disk Access: Likely OK`
  - `App state: launching`
  - `Stored credentials: No`
- Later retries of `kakaocli status` hung for 20+ seconds
- `kakaocli login --status` also hung for 20+ seconds and had to be terminated

Interpretation:
- app lifecycle detection is not stable in this environment
- this is a secondary problem
- the main RAG blocker is still failed `auth`

## Local Files and Paths Observed

### KakaoTalk container preferences

Found container prefs at:

```text
/Users/alice/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Preferences/com.kakao.KakaoTalkMac.C7FA3FEBE58F93FF46840951B09DAF7043163471.plist
```

Important finding:
- there are **no** keys matching `FSChatWindowTransparency...`
- there are **no** direct keys like `userId`, `user_id`, `KAKAO_USER_ID`, or `userID`

### KakaoTalk application support

Found these notable entries under:

```text
/Users/alice/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Application Support/com.kakao.KakaoTalkMac
```

Relevant items:
- `656eb056ef94e6a79dadeb51fe506f9698e8e7d85a02f5e25c70b536b9337a71017d7c5fc0393a`
- `656eb056ef94e6a79dadeb51fe506f9698e8e7d85a02f5e25c70b536b9337a71017d7c5fc0393a-wal`
- `656eb056ef94e6a79dadeb51fe506f9698e8e7d85a02f5e25c70b536b9337a71017d7c5fc0393a-shm`
- `4040b3ef0540ad103832d13e686b031be1c9d650/`

Important finding:
- the filename `656e...0393a` is 78 hex chars long
- `kakaocli`'s source derives DB filenames as 78-char hex strings
- this strongly suggests the DB file **does exist**
- but `kakaocli` cannot derive the correct name because it lacks the correct `userId`

## Source-Code Evidence From kakaocli

Source reviewed from the upstream repo:
- repo: `silver-flight-group/kakaocli`

### 1. `DeviceInfo.userId()` is too narrow

File:
- `Sources/KakaoCore/Database/DeviceInfo.swift`

Current logic:
- check the container plist first, then the global plist
- extract user ID only by:
  - finding multiple keys with prefix `FSChatWindowTransparency` and taking the common suffix
  - or direct key lookup from one of:
    - `userId`
    - `user_id`
    - `KAKAO_USER_ID`
    - `userID`

If neither path works, it throws:

```text
Could not find user ID in plist
```

Why this matters:
- the current KakaoTalk plist on this Mac does not expose either pattern
- therefore `auth` fails before DB decryption even starts

### 2. `AuthCommand` depends completely on that `userId`

File:
- `Sources/KakaoCLI/Commands/AuthCommand.swift`

Current flow:
1. read platform UUID
2. read `userId`
3. derive database filename
4. derive SQLCipher key
5. open DB

Failure point on this Mac:
- step 2

Consequence:
- DB filename and decryption key are never derived correctly
- all DB-backed read commands remain blocked

### 3. `KeyDerivation.databaseName()` shows the DB file is plausibly present

File:
- `Sources/KakaoCore/Database/KeyDerivation.swift`

Important implementation detail:
- `databaseName(userId:uuid:)` returns a 78-char hex filename

Observed local evidence:
- existing file `656eb056ef94e6a79dadeb51fe506f9698e8e7d85a02f5e25c70b536b9337a71017d7c5fc0393a` is exactly 78 chars

Inference:
- local DB presence is plausible
- the unresolved problem is not "no database"
- the unresolved problem is "wrong or missing userId for deriving the right DB path and SQLCipher key"

### 4. `StatusCommand` underreports preference state for containerized installs

File:
- `Sources/KakaoCLI/Commands/StatusCommand.swift`

Current behavior:
- `Preferences exist` checks only:
  - `~/Library/Preferences/com.kakao.KakaoTalkMac.plist`

But in this environment, the richer data lives under:
- `~/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Preferences/...`

Effect:
- `status` can say `Preferences exist: No` even though useful container prefs do exist
- this makes diagnosis noisier

## Why RAG Is Not Currently Possible

RAG requires a reliable read path such as:

```bash
kakaocli chats --json
kakaocli messages --chat "..." --json
kakaocli search "..." --json
kakaocli query "SELECT ..." --json
```

Those commands require:
- correct database filename
- correct SQLCipher key
- successful DB open

Current state:
- `auth` cannot discover the needed `userId`
- therefore the DB-backed commands are still blocked

So:
- UI inspection works
- chat list visibility works
- but **message-conversation RAG does not work yet**

## False Leads Already Checked

These were tested and did not solve the problem:

- installing Xcode and making it active
- verifying `kakaocli` installation
- re-running `status`
- re-running `auth`
- using numeric IDs from `AlertKakaoIDsList` as `--user-id`
- checking both global and container KakaoTalk plist locations
- checking whether `harvest` could bootstrap the situation

Important note about `harvest`:
- it is **not** a workaround here
- `HarvestCommand` still resolves and opens the DB first
- so it cannot bypass failed `auth`

## Most Likely Root Cause

Most likely root cause:
- `kakaocli 0.5.0` assumes an older or narrower KakaoTalk preference layout for extracting the local account `userId`
- the installed KakaoTalk build on this Mac stores account state differently
- as a result, `kakaocli` cannot compute the correct DB name and key, even though the account appears logged in and the DB likely exists

## Recommended Next Investigation for Another AI

### Highest-priority fix path

Patch `DeviceInfo.userId()` in `kakaocli` to support the current KakaoTalk local state on this Mac.

Suggested work items:

1. Inspect the container plist deeply for alternate account representations
   - especially binary plist or blob values that may encode the current user profile or account ID
   - likely places are the container plist values already confirmed present

2. Add fallback discovery logic beyond:
   - `FSChatWindowTransparency...`
   - direct `userId` keys

3. Rebuild `kakaocli`

4. Re-test:

```bash
kakaocli auth
kakaocli chats --json
kakaocli messages --chat "조민석" --since 7d --json
kakaocli search "..." --json
```

### Secondary fix path

Improve lifecycle/status behavior:
- make `status` check container preferences too
- investigate why `status` and `login --status` sometimes hang on this machine

## Minimal Reproduction Set

If another AI wants the shortest useful repro sequence, use:

```bash
xcode-select -p
xcodebuild -version
command -v kakaocli
brew list --versions kakaocli
kakaocli auth
defaults read com.kakao.KakaoTalkMac
plutil -p ~/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Preferences/com.kakao.KakaoTalkMac.C7FA3FEBE58F93FF46840951B09DAF7043163471.plist
find ~/Library/Containers/com.kakao.KakaoTalkMac/Data/Library/Application\\ Support/com.kakao.KakaoTalkMac -maxdepth 1 -print
```

## Bottom Line

The blocker is **not**:
- missing installation
- missing Xcode
- obvious lack of KakaoTalk login

The blocker **is**:
- `kakaocli` cannot discover the correct Kakao `userId` from the current KakaoTalk local state
- therefore it cannot derive the DB filename or SQLCipher key
- therefore DB-backed read commands required for RAG do not work
