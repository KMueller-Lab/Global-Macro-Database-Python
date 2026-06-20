# Bug 修复对应表

根据原始 bug 列表逐项检查当前 commits 中的实际修复。

---

## Bug 1: Listed versions return 404 (P0)

**问题：** versions.csv 列出 9 个版本，5 个返回 404

**当前代码修复：** ❌ **未修复**
- 这是数据问题，不是代码问题
- 用户验证：重新运行后所有版本都能下载（上游已修复）

**涉及 commits：** 无

---

## Bug 2: country=840 (int) leaks TypeError (P1)

**问题：**
```python
>>> gmd(country=840)
TypeError: 'int' object is not iterable  # ❌ 未被包装
```

**当前代码修复：** ✅ **已修复**
- 第 425-435 行：添加 isinstance 类型检查

**改动代码：**
```python
# Type check for country and variables parameters
if country is not None and not isinstance(country, (str, list)):
    raise GMDCommandError(
        f"country must be a string, list, or None, not {type(country).__name__}",
        code=198
    )
if variables is not None and not isinstance(variables, (str, list)):
    raise GMDCommandError(
        f"variables must be a string, list, or None, not {type(variables).__name__}",
        code=198
    )
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

## Bug 3: get_available_versions() leaks RuntimeError (P1)

**问题：**
```python
>>> get_available_versions()
RuntimeError: Unable to load 'helpers/versions.csv'.  # ❌ 内部异常泄露
```

**当前代码修复：** ✅ **已修复**
- 第 362-373 行：RuntimeError 被包装成 GMDCommandError

**改动代码：**
```python
def get_available_versions() -> List[str]:
    try:
        return _versions_df()["versions"].astype(str).tolist()
    except RuntimeError as e:
        versions = _cache_versions()
        if versions:
            return versions
        if _default_local_gmd_path() is not None:
            return ["local"]
        raise GMDCommandError(  # ✅ RuntimeError 被正确包装
            f"Unable to access version information. {str(e)}",
            code=498
        ) from e
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

## Bug 4: raw/fast/iso accept any truthy string (P1)

**问题：**
```python
>>> gmd(country="USA", variables="rGDP", raw="no")     # ❌ 也加载原始数据
>>> gmd(country="USA", variables="rGDP", fast="1")     # ❌ 不缓存
>>> gmd(iso="no")                                       # ❌ 也返回列表
```

**当前代码修复：** ✅ **已修复**
- 第 385-397 行：新增 `_coerce_flag()` 函数，白名单验证
- 第 438-441 行：所有标志位都调用 `_coerce_flag()` 进行规范化

**改动代码：**
```python
def _coerce_flag(value: Union[bool, str, None]) -> bool:
    """Convert bool/str flag to bool. Accepts: True/'yes'/'true'/'1' -> True; False/'no'/'false'/'0' -> False."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).lower().strip()
    if s in ("yes", "true", "1", "on"):
        return True
    if s in ("no", "false", "0", "off"):
        return False
    raise GMDCommandError(f"Invalid flag value: {value}. Use True/False or 'yes'/'no'.", code=198)

# 在函数入口处
raw = _coerce_flag(raw)
iso = _coerce_flag(iso)
fast_unset = fast is None
fast = _coerce_flag(fast)
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

## Bug 5: start_year unknown-kwarg error leaks raw TypeError (P2)

**问题：**
```python
>>> gmd(country="USA", variables="rGDP", start_year=2000)
TypeError: Unexpected keyword argument(s): start_year  # ❌ 未被包装，参数无效
```

**当前代码修复：** ✅ **已修复**
- 第 414-415 行：添加 start_year/end_year 为一等参数
- 第 444-449 行：参数类型验证（包装成 GMDCommandError）
- 第 800+ 行：实现年份过滤逻辑

**改动代码：**
```python
def gmd(
    ...
    start_year: Optional[int] = None,        # ✅ 现在是正式参数
    end_year: Optional[int] = None,          # ✅ 现在是正式参数
    **kwargs,
) -> Optional[pd.DataFrame]:
    ...
    # Validate year parameters
    if start_year is not None and not isinstance(start_year, int):
        raise GMDCommandError("start_year must be an integer or None", code=198)
    if end_year is not None and not isinstance(end_year, int):
        raise GMDCommandError("end_year must be an integer or None", code=198)
    if start_year is not None and end_year is not None and start_year > end_year:
        raise GMDCommandError("start_year must be <= end_year", code=198)
```

**年份过滤实现：**
```python
if (start_year is not None or end_year is not None) and df is not None:
    if "year" in df.columns:
        if start_year is not None:
            df = df[df["year"] >= start_year]
        if end_year is not None:
            df = df[df["year"] <= end_year]
        df = df.reset_index(drop=True)
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

## Bug 6: Design-level gaps (P2+)

### 6a. 重试机制和指数退避 ✅

**问题：** 原代码无重试，单次网络故障即失败

**修复位置：** 第 99-115 行

**改动代码：**
```python
def _fetch_from(relative_path: str, bases: Sequence[str]) -> requests.Response:
    errors: List[str] = []
    headers = {"User-Agent": _USER_AGENT}
    for base in bases:
        url = f"{base}/{relative_path}"
        for attempt in range(3):  # ✅ 最多 3 次尝试
            try:
                response = requests.get(url, timeout=_TIMEOUT_SECONDS, headers=headers)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if attempt < 2:
                    wait_time = 2 ** attempt  # ✅ 指数退避
                    time.sleep(wait_time)
                else:
                    errors.append(f"{url}: {exc}")
    raise RuntimeError(...)
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6b. User-Agent 标识 ✅

**问题：** 服务器无法识别客户端

**修复位置：** 第 23 行 + 第 101 行

**改动代码：**
```python
_USER_AGENT = "global-macro-data/2.0.0 (+https://github.com/KMueller-Lab/Global-Macro-Database-Python)"
...
headers = {"User-Agent": _USER_AGENT}
response = requests.get(url, timeout=_TIMEOUT_SECONDS, headers=headers)
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6c. 超时时间优化 ✅

**问题：** timeout=60 秒太长

**修复位置：** 第 22 行

**改动代码：**
```python
_TIMEOUT_SECONDS = 15  # ✅ 从 60 改为 15
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6d. 大小验证和完整性检查 ✅

**问题：** 部分下载未被检测，缓存被污染

**修复位置：** 第 134-154 行

**改动代码：**
```python
def _read_dta(resp: requests.Response) -> Tuple[pd.DataFrame, Path]:
    content = resp.content
    headers = getattr(resp, "headers", {}) or {}
    expected_size = int(headers.get("Content-Length", 0))  # ✅ 读期望大小

    temp_file = _CACHE_DIR / f"tmp_{uuid.uuid4().hex}.dta"
    temp_file.write_bytes(content)

    # Validate size
    if expected_size > 0 and temp_file.stat().st_size != expected_size:  # ✅ 大小验证
        temp_file.unlink()
        raise ValueError(...)

    # Validate readability
    try:
        df = pd.read_stata(temp_file, convert_categoricals=False)  # ✅ 完整性检查
        return df, temp_file
    except Exception as e:
        temp_file.unlink()
        raise ValueError(...)
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6e. 原子文件写入 ✅

**问题：** 缓存文件部分写入时程序崩溃

**修复位置：** 第 753-754 行

**改动代码：**
```python
df, temp_file = _read_dta_primary(f"distribute/GMD_{selected_version}.dta")
...
shutil.move(str(temp_file), str(local_version))  # ✅ 原子操作
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6f. 缓存失效机制 ✅

**问题：** 远程版本更新时，本地缓存不会失效

**修复位置：** 第 741 行 + 第 196-207 行

**改动代码：**
```python
# 缓存文件包含版本号
local_version = _CACHE_DIR / f"GMD_{selected_version}.dta"  # ✅ 版本号纳入文件名

# 扫描本地版本
pattern = re.compile(r"^GMD_(\d{4}_\d{2})\.dta$")
for path in _CACHE_DIR.glob("GMD_*.dta"):
    match = pattern.match(path.name)
    if match:
        versions.append(match.group(1))
```

**自动失效原理：** 版本不同 → 文件名不同 → 无覆盖风险

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支)

---

### 6g. VALID_VARIABLES 前置验证 ✅

**问题：** 无效变量名需下载完整 21 MB 数据才被发现

**修复位置：** 第 471-476 行

**改动代码：**
```python
if anything_tokens and sources is None:
    # ... 识别列检查 ...
    
    # ✅ 在下载前验证变量名
    invalid = [v for v in anything_tokens if v not in VALID_VARIABLES]
    if invalid:
        raise GMDCommandError(
            "Specified variable is not valid.",
            code=198,
        )
```

**涉及 commits：** 
- `7d294b4` fix: VALID_VARIABLES check, fast_unset hint, GMD.dta test
- `a8b55f1` fix: identifying variable error message and skip VALID_VARIABLES check for sources mode

---

### 6h. setup.py 版本下界 ✅

**问题：** 依赖项无下界版本限制

**修复位置：** setup.py 第 13 行

**改动代码：**
```python
install_requires=[
    "requests>=2.20.0",  # ✅ 加入下界
    "pandas>=1.0.0",     # ✅ 加入下界
],
```

**涉及 commits：** 
- `195cadf` fixed all bugs (主分支) 中包含的改动

---

### 6i. CI 测试矩阵 ✅

**问题：** 代码声称支持 Python 3.8+，但无测试覆盖

**修复位置：** .github/workflows/test.yml

**改动代码：**
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]  # ✅ 完整覆盖
steps:
  - run: pip install -e .
  - run: pip install pytest  # ✅ 分离安装
  - run: pytest tests/
```

**涉及 commits：** 
- `ec94637` fix CI: install pytest directly, add fail-fast false
- `69a3368` fix CI: split pip install steps

---

### 6j. setup.py author 属性 ⚠️

**问题：** author="Yangbo Wang" 与包的实际作者不一致

**当前状态：** ⚠️ **未修改（待上游决定）**

**涉及 commits：** 无

---

## 修复总结

| Bug # | 问题 | P | 状态 | 涉及 commits |
|-------|------|---|------|-------------|
| 1 | versions 404 | 0 | ✅ 上游数据已修 | — |
| 2 | country=840 | 1 | ✅ 已修 | 195cadf |
| 3 | RuntimeError | 1 | ✅ 已修 | 195cadf |
| 4 | 标志位 | 1 | ✅ 已修 | 195cadf |
| 5 | start_year | 2 | ✅ 已修 | 195cadf |
| 6a | 重试 | 2 | ✅ 已修 | 195cadf |
| 6b | User-Agent | 2 | ✅ 已修 | 195cadf |
| 6c | 超时 | 2 | ✅ 已修 | 195cadf |
| 6d | 大小验证 | 2 | ✅ 已修 | 195cadf |
| 6e | 原子写入 | 2 | ✅ 已修 | 195cadf |
| 6f | 缓存失效 | 2 | ✅ 已修 | 195cadf |
| 6g | VALID_VARIABLES | 2 | ✅ 已修 | 7d294b4, a8b55f1 |
| 6h | 版本下界 | 2 | ✅ 已修 | 195cadf |
| 6i | CI 矩阵 | 2 | ✅ 已修 | ec94637, 69a3368 |
| 6j | author 属性 | 2 | ⚠️ 未修 | — |

**总计修复率：** 93% (14/15)

---

## 问题分析

**为什么 git commits 简介不清楚？**

1. **主要修复 "hidden" 在主分支** 
   - `195cadf` "fixed all bugs" 是主分支中的一个 commit
   - 它包含 Bug 1-6a 到 6h 的大部分修复
   - 但当前分支（HEAD~7）没有直接包含它，需要通过 git merge/rebase 看

2. **当前分支的 7 个 commits 职责混合**
   - 3aa5163 debug（无意义）
   - ec94637, 69a3368（CI 修复，对应 Bug 6i）
   - 91b6742（处理 identifying variables，未在原 bug 列表中）
   - 7d294b4, a8b55f1（VALID_VARIABLES 验证，对应 Bug 6g）
   - d1af1cd（文档）

3. **缺少对 main 分支修复的声明**
   - 主要的 bugs 2-6h 在 `195cadf` 中修复
   - 但这个 commit 不在当前分支的 git log 中显示

---

## 建议

应该**重新组织 commits**，让每个 commit 清楚地对应一个或一组 bug：

```
Commit 1: fix(Bug 2,3): Type validation and exception wrapping
  - country/variables isinstance check
  - get_available_versions RuntimeError → GMDCommandError

Commit 2: fix(Bug 4): Add _coerce_flag() for consistent flag handling
  - raw/fast/iso whitelist validation
  - Reject invalid flag values

Commit 3: fix(Bug 5): Add start_year/end_year parameters and filtering
  - Year range parameter validation
  - Implement year filtering logic

Commit 4: fix(Bug 6a-6f): Network resilience and cache improvements
  - Retry with exponential backoff (3 attempts)
  - User-Agent header
  - Timeout optimization (60s → 15s)
  - Size validation and completeness check
  - Atomic file writes with shutil.move()
  - Version-aware cache invalidation

Commit 5: fix(Bug 6g): VALID_VARIABLES front-end validation
  - Check variables before download
  - Skip check for sources mode

Commit 6: fix(Bug 6h): Add version bounds for dependencies
  - requests>=2.20.0, pandas>=1.0.0

Commit 7: fix(Bug 6i): Expand CI test matrix
  - Python 3.8-3.12 coverage
  - Split pip install steps
  - fail-fast: false

Commit 8: docs: Add comprehensive bug fix summary
  - Document all fixes with details
  - Map to code locations
```
