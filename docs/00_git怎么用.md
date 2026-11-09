# git 怎么用（零基础 · 本项目专用）

> 写给完全没用过 git 的三个人。看完这一份，够你们用到 11-28。
> 不用背命令，把最后那页「一页速查」打印出来贴在桌上就行。

---

## 0. 一句话理解 git

**git 是给文件夹装了一台时光机。**

你每改一次代码，就按一下「存档」（commit）。以后任何时候都能：

- 看昨天那版长什么样
- 把今天的改动撤掉，回到昨天
- 知道"这行代码是谁改的、为什么改"

**它不是什么：** 不是网盘，不是自动备份，不会自动帮你保存。**你不按存档，它就不记。**

### 三个词，记住就能干活

```
你的文件夹  ──git add──>  待提交清单  ──git commit──>  存档（历史里）
  （改这里）                （挑哪些要存）              （永久记下）
```

| 词 | 意思 | 类比 |
|---|---|---|
| **工作区** | 你正在编辑的那些文件 | 桌上摊开的稿纸 |
| **暂存区**（add 之后） | 你挑出来"这次要存档"的改动 | 装进档案袋的那几页 |
| **提交**（commit） | 一次永久存档，带一句说明 | 档案袋封口、写上日期 |
| **推送**（push） | 把本地存档同步到服务器 | 把档案袋寄到档案室 |

---

## 1. 先解决最大的问题：三个人的仓库怎么连起来

⚠️ **这一步不做，git 对你们毫无用处。**

现在 `racecar/` 这个 git 仓库**只存在于当前这台电脑上**。A 和 B 的电脑上什么都没有，他们改的东西你也看不见。

所以必须先有一个「远端仓库」（remote）——一个三个人都能访问的服务器地址。

### 1.1 选哪个

| 方案 | 优点 | 缺点 | 建议 |
|---|---|---|---|
| **Gitee（码云）** | 国内快、私有仓库免费、注册用手机号 | 需要实名 | ✅ **首选** |
| GitHub | 生态好 | 国内经常连不上 | 备用 |
| 局域网共享盘 | 不用注册 | 会互相覆盖文件、`.git` 在共享盘上容易锁死 | ❌ 别用 |
| 每天发 zip 到群里 | 零成本 | 三天后没人知道哪版是对的 | ❌ 别用 |

**结论：用 Gitee，建一个私有仓库。**

### 1.2 建仓库（由一个人做，建议 C）

1. 打开 https://gitee.com ，注册（手机号即可）
2. 右上角 `+` → **新建仓库**
3. 填写：
   - 仓库名称：`racecar`
   - **是否开源：私有**（很重要，比赛期间别公开）
   - **不要**勾选「使用 Readme 初始化仓库」（会跟本地文件打架）
4. 建好后页面会给一个地址，形如：
   `https://gitee.com/你的用户名/racecar.git`

### 1.3 把本地代码推上去（在 racecar 目录里执行）

```powershell
cd C:\Users\ASUS\Documents\deepseek-harness\default-workspace\racecar

git remote add origin https://gitee.com/你的用户名/racecar.git
git branch -M main
git push -u origin main
```

> 第一次 push 会弹窗要账号密码。**密码填 Gitee 的「私人令牌」，不是登录密码** ——
> Gitee → 设置 → 私人令牌 → 生成新令牌（勾 `projects` 权限）→ 复制那串字符当密码用。

### 1.4 另外两个人把仓库拉下来

A 和 B 在**自己电脑**上，装好 git 后：

```powershell
cd D:\            # 或者任何你想放的位置
git clone https://gitee.com/你的用户名/racecar.git
cd racecar

git config user.name  "张三"
git config user.email "zhangsan@example.com"
```

> 这两行 `config` 每人**只需做一次**，作用是让你提交的记录上显示你的名字。
> 不配的话，提交记录会显示成别人的名字，出问题找不到人。

### 1.5 验证一下

```powershell
git log --oneline -3
git remote -v
```

能看到提交记录、能看到 `origin` 地址，就通了。

---

## 2. 八条命令，够用 20 天

| 命令 | 干什么 | 什么时候用 |
|---|---|---|
| `git status` | 看现在有哪些改动没存档 | **最常用**，随时敲 |
| `git pull` | 把队友的改动拉下来 | **每天开工第一件事** |
| `git add -A` | 把所有改动放进待提交清单 | 改完之后 |
| `git commit -m "说明"` | 存档 | 改完之后 |
| `git push` | 推给服务器（队友才能看到） | 每天收工 |
| `git log --oneline -5` | 看最近 5 次存档 | 想不起来改了啥时 |
| `git diff` | 看具体改了哪几行 | 提交前检查 |
| `git checkout -- 文件` | 撤销某个文件的改动 | 改坏了 |

**就这些。** 网上那些 `rebase`、`stash`、`cherry-pick`…… 20 天内你们一个都用不上，别学。

---

## 3. 一个人的日常节奏

每次改代码，重复这个循环：

```powershell
# ① 开工（每天早上第一件事，不做这步必冲突）
git pull

# ② 干活……改代码、调参数、跑车

# ③ 看看自己改了什么
git status
git diff

# ④ 存档
git add -A
git commit -m "直线循迹：P=8 D=0.5 速度40%，10次过7次"

# ⑤ 推给队友
git push
```

**一句话记住：早上 pull，晚上 push。**

---

## 4. 三个人的节奏（这条最容易出事）

### 铁规则一：一人一目录

| 人 | 只改 |
|---|---|
| A | `docs/`、`logs/`、`media/`、接线相关 |
| B | `vision/` 里的东西 |
| C | `firmware/`、`tools/` |

**两个人同时改同一个文件 = 冲突。** 冲突不是灾难，但会浪费你们半小时，而且容易改错。

### 铁规则二：`config.py` / `config.h` 只由一个人改

这两个文件是所有参数的集中地，**一定会被两个人同时想改**。约定好：

- 谁负责调车谁改，改完立刻 `commit + push`
- 另一个人要用新参数，先 `git pull`

### 铁规则三：每天至少有一个人 push

如果三个人都在本地攒着不推，第二天一 `pull`，会出现一屏看不懂的东西。

---

## 5. 提交信息怎么写（这条决定 git 有没有用）

### 公式

```
改了什么 + 为什么改 + 结果如何
```

### 好的例子（照这个写）

```
直线循迹：P 从 6 调到 8，10 次过 7 次（原来 4 次）
修右电机反转：AIN1/AIN2 接反，改线后正反转正常
指示牌阈值降到 40：室内灯光下误触发从 5 次/分钟降到 0
加超声避障：35cm 内右转绕行，测试 5 次成功 4 次
颜色顺序改为从右往左读：实车装的是反的，改 ORDER_REVERSED
```

### 坏的例子（等于没写）

```
改了一下
更新
fix
123
最终版
最终版2
真的最终版
```

> 三个月后你回来看 `fix`，你会想知道当时那个人（就是你自己）在想什么。

---

## 6. tag：交付节点的存档点

`tag` 是给某次存档贴一个永久标签，用来标记「这个版本能演示 X」。

```powershell
git tag v0.2-直线
git push origin v0.2-直线
```

对应 [README](../README.md) 里的节点表：

| 日期 | tag |
|---|---|
| 11-11 | `v0.1-上电` |
| 11-14 | `v0.2-直线` |
| 11-18 | `v0.3-过弯` |
| 11-21 | `v0.4-指示牌` |
| 11-25 | `v0.5-串通` |
| 11-27 | `v1.0-封存` ← **比赛用的就是这个** |

**为什么 11-28 那天 tag 很关键：** 细则要求"只用封存版本"。打了 tag，你能证明比赛当天跑的代码和 11-27 封存的一模一样，没有临场偷改。

---

## 7. 冲突：那一屏 `<<<<<<<` 别慌

### 什么时候会发生

你和队友改了**同一个文件的同一片区域**，然后你 `git pull`，git 不知道该听谁的。

```
Auto-merging firmware/Core/Inc/config.h
CONFLICT (content): Merge conflict in firmware/Core/Inc/config.h
Automatic merge failed; fix conflicts and then commit the result.
```

### 三步处理法

**第一步：打开那个文件**，会看到：

```c
<<<<<<< HEAD
#define SPEED_BASE   420
=======
#define SPEED_BASE   380
>>>>>>> origin/main
```

意思：`<<<<<<<` 到 `=======` 是**你**的版本，`=======` 到 `>>>>>>>` 是**队友**的版本。

**第二步：人工决定要哪个**，把三个标记行全删掉，只留最终要的那行：

```c
#define SPEED_BASE   380
```

> 拿不准就打电话问队友。**这是人的决定，git 不替你做。**

**第三步：存档**

```powershell
git add -A
git commit -m "合并：速度取 380（队友实测更稳）"
git push
```

### 预防（比处理重要 10 倍）

1. 每天开工先 `git pull`
2. 一人一目录，别改别人的文件
3. `config.h` / `config.py` 只一个人改

---

## 8. 灾难急救（五种，都见过）

### ① 改坏了，想回到昨天那版

```powershell
git log --oneline -5          # 找到昨天的存档号，比如 a1b2c3d
git checkout a1b2c3d -- .     # 把整个目录恢复成那版（会覆盖当前改动！）
```

只恢复一个文件：

```powershell
git checkout a1b2c3d -- firmware/Core/Src/app.c
```

### ② 只想扔掉还没提交的改动

```powershell
git checkout -- 文件名        # 单个文件
git checkout -- .             # 全部（危险，会丢所有未提交改动）
```

### ③ commit 信息写错了

```powershell
git commit --amend -m "正确的说明"
```

> 只能改**最近一次**，而且**还没 push** 的时候改。已经 push 了就别改了，将错就错。

### ④ 不小心提交了不该提交的（缓存、视频、密码）

```powershell
git rm -r --cached __pycache__
git rm --cached media/测试视频.mp4
git commit -m "移除误提交的缓存文件"
```

> 文件还在硬盘上，只是从 git 里踢出去。
> **密码/令牌一旦提交过，就算删了也留在历史里 —— 立刻去平台改密码。**

### ⑤ push 被拒绝（`rejected` / `non-fast-forward`）

说明队友先推了东西，你落后了。

```powershell
git pull
# 如果有冲突，按第 7 节处理
git push
```

⚠️ **绝对不要**用 `git push -f`。那会把队友的提交直接抹掉，而且找不回来。

### ⑥ 想看某行代码是谁改的

```powershell
git log -p firmware/Core/Inc/config.h    # 这个文件每次改了什么
git blame firmware/Core/Src/app.c        # 每一行是谁、哪次改的
```

---

## 9. Windows 上的五个坑

### 坑 1：`warning: LF will be replaced by CRLF`

**忽略它。** 这是 Windows 和 Linux 换行符不一样导致的提示，不影响任何东西。
项目里已经有 `.gitattributes` 在处理，看到就当没看到。

### 坑 2：中文文件名显示成 `\346\226\207\344\273\266`

```powershell
git config --global core.quotepath false
```

### 坑 3：PowerShell 里 `-m` 后面的引号

```powershell
git commit -m "直线：P=8"        # ✅ 这样
git commit -m "直线："P=8""      # ❌ 会报错
```

说明里要用引号，就用中文引号 `「」` 或单引号。

### 坑 4：**别把仓库放在 OneDrive / 百度网盘同步目录里**

同步盘会在 git 改文件时插一脚，导致 `.git` 里的文件被锁、仓库损坏。
`racecar/` 放在 `D:\` 或 `C:\Users\你\Documents\` 这种普通目录就行。

### 坑 5：中文路径

路径里带中文本身没问题，但**编译工具链**（Keil、CubeIDE）遇到中文路径容易报奇怪的错。
所以项目目录叫 `racecar`（英文），这点已经做对了。

---

## 10. 树莓派上怎么用

树莓派上**只做两件事**：拉代码、跑代码。

```bash
sudo apt install -y git
git clone https://gitee.com/你的用户名/racecar.git
cd racecar/vision

# 以后更新
cd ~/racecar && git pull
```

⚠️ **树莓派上一般不要 commit。** 万一你在树莓派上改了 `config.py` 调阈值，改完记得在**电脑上**同步一份，否则两边不一致，几天后你会疯。

---

## 11. 六件不要做的事

| ❌ 不要 | 为什么 |
|---|---|
| `git push -f` | 抹掉队友的提交，不可恢复 |
| 提交 `__pycache__`、`.hex`、`.o` | 无意义二进制，仓库越滚越大（`.gitignore` 已挡） |
| 提交 4K 视频 | 一个 200MB 视频能让 `clone` 变成 10 分钟 |
| 提交密码、令牌、WiFi 密码 | 历史里删不掉，等于公开 |
| 两个人同时改 `config.h` | 100% 冲突 |
| 三天不 push | 攒一堆改动，一次合并炸掉 |

---

## 12. 一页速查（建议打印）

```
┌──────────────────────────────────────────────────────────┐
│  每天早上（第一件事）                                     │
│      git pull                                            │
│                                                          │
│  每次改完代码                                            │
│      git status            看看改了啥                    │
│      git add -A            全都要存                      │
│      git commit -m "改了什么+为什么+结果"                │
│                                                          │
│  每天收工                                                │
│      git push              推给队友                      │
│                                                          │
│  到达交付节点                                            │
│      git tag v0.2-直线                                   │
│      git push origin v0.2-直线                           │
│                                                          │
│  改坏了                                                 │
│      git checkout -- 文件名       扔掉未提交的改动       │
│      git log --oneline -5         找历史版本             │
│      git checkout 版本号 -- .     整体回到那版           │
│                                                          │
│  出现 <<<<<<< 冲突                                       │
│      打开文件 → 删掉三个标记行 → 只留要的 → add+commit   │
│                                                          │
│  三条铁律                                                │
│      一人一目录 · 每天早上 pull · 绝不 push -f           │
└──────────────────────────────────────────────────────────┘
```

---

## 附录：常见报错翻译

| 英文报错 | 中文意思 | 怎么办 |
|---|---|---|
| `not a git repository` | 你不在仓库目录里 | `cd` 到 `racecar` 目录 |
| `Please tell me who you are` | 没配名字邮箱 | 跑第 1.4 节那两行 `git config` |
| `rejected ... non-fast-forward` | 队友先推了 | `git pull` 再 `push` |
| `CONFLICT (content)` | 冲突 | 见第 7 节 |
| `Your local changes would be overwritten` | 你有未提交的改动，pull 会覆盖 | 先 `commit` 或 `checkout -- .` |
| `Permission denied (publickey)` | SSH 密钥没配 | 改用 https 地址克隆 |
| `fatal: refusing to merge unrelated histories` | 两边历史不相干（初始化方式不同） | `git pull origin main --allow-unrelated-histories` |

---

## 附：这个仓库现在是什么状态

```
仓库位置：  C:\Users\ASUS\Documents\deepseek-harness\default-workspace\racecar
当前分支：  main（原 master，已改名）
首次提交：  091c5d5  init: 项目骨架 + 接口协议 v1.0
已跟踪文件：39 个
远端：      还没有（需要你们按第 1.3 节建 Gitee 仓库）
```

**下一步就一件事：建 Gitee 私有仓库，把 1.3 节那三行命令敲下去。**
做完这一步，git 才开始为你们工作。
