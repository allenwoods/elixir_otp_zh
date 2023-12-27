# 11 基于属性和并发性的测试

本章包括：

- 使用QuickCheck进行基于属性的测试
- 使用Concuerror检测并发错误

在这最后一章（万岁！），我们继续调查一些可用的测试工具。你刚刚看到了ExUnit和Dialyzer。然而，Erlang生态系统还有更多的东西可以提供，正如接下来的部分将展示的那样。

首先，有QuickCheck，这是一个基于属性的测试工具。基于属性的测试将单元测试颠倒过来。与传统的单元测试编写*特定*的测试用例不同，基于属性的测试强迫你以*一般*规范的形式表达你的测试用例。一旦你有了这些规范，这个工具就可以生成你心中期望的尽可能多的测试用例。

接下来，我们将看一下Concuerror。Concuerror是一个系统地检测你的程序中并发错误的工具。Concuerror可以指出难以检测和经常令人惊讶的竞态条件、死锁和潜在的进程崩溃。

本章包含大量的例子供你尝试，提供了充足的机会让你感受这些工具。当你的程序开始变得复杂时，这些工具可以为你的程序提供令人难以置信的洞察力。让我们开始提升我们的测试技能吧！

11.1       基于属性的测试和QuickCheck简介

面对现实 - 单元测试可能是一项艰巨的工作。你经常需要考虑几种情况，并确保覆盖所有的边缘情况。你需要考虑像垃圾数据、极端值和懒惰的程序员只想以最愚蠢的方式通过测试的情况。如果我告诉你，你可以通过编写*规范*来*生成*测试用例，而不是手动编写单个测试用例，你会怎么想？这就是基于属性的测试的全部内容。

下面是一个快速的例子：假设我们正在测试一个排序函数。在单元测试领域，我们会想出不同的列表示例，如：

`·`
`[3, 2, 1, 5, 4]`

`·`
`[3, 2, 4, 4, 1, 5, 4] # 有重复的`

`·`
`[1, 2, 3, 4, 5]       # 已经排序了`

你能想到我们可能遗漏的其他情况吗？在我脑海中，我们遗漏了像空列表和包含负整数的列表这样的情况。说到整数，其他数据类型如原子或元组呢？如你所见，这开始变得繁琐，且遗漏某些边缘情况的概率大大增加。

使用基于属性的测试，我们可以指定排序函数的属性。例如，对列表排序一次与对列表排序两次是一样的。我们可以像这样指定一个属性（暂时不用担心语法）：

清单 11.1 列表排序的一个示例属性

`@tag numtests: 1000`
`property "sorting twice will yield the same result" do`
`forall l <- list(int) do`
`ensure l |> Enum.sort == l |> Enum.sort |> Enum.sort`
`end``end`
这个属性生成了*一千*种不同的整数列表，并确保这个属性对每个列表都成立。如果属性失败，工具会自动*缩小*测试用例，找到使同一属性失败的最小列表。

我们将要使用的工具是QuickCheck。准确地说，我们将使用Quviq开发的Erlang QuickCheck。虽然Erlang QuickCheck的完整版本需要商业许可，但我们将使用的是一个缩小版的Erlang QuickCheck *Mini*。

Quviq QuickCheck的付费版和免费版有什么区别？

两个版本都支持基于属性的测试，这是这个工具的全部要点！付费版本有其他的优点，比如使用状态机进行测试，并行执行测试用例以检测竞态条件（我们将有Conqueror来处理这个问题），当然还有商业支持。

你应该知道，除了Erlang QuickCheck，还有一些类似的基于属性的测试工具可用：

- Triform QuickCheck 或 *Triq* [[1]](#u83UNuzRV57fRwEzhWNgBm6)
- PropEr[[2]](#uzOPdfenDvyvCoAdHdYLuV8): 一个受QuickCheck启发的Erlang的基于属性的测试工具

Quivq的版本可以说是这三个中最成熟的。虽然免费版本在功能上有些限制，但对我们的目的来说已经足够了。一旦你掌握了基础知识，你可以轻松地转向其他版本的QuickCheck，因为概念是相同的，语法也相似。让我们开始在我们的系统上安装QuickCheck。

11.1.1     安装 QuickCheck

安装 QuickCheck 比通常的 Elixir 依赖稍微复杂一些，但并不困难。首先，前往 Quviq[[3]](#utP7ZYyoYEcEE26GeQaeT75) 并下载 QuickCheck (Mini) 的*免费*版本。除非你有有效的许可证，否则你应该下载免费版本，否则你会被提示输入许可证。一旦你下载了文件，就可以按照以下步骤操作：

·      解压文件并
`cd`
进入结果文件夹

·      运行
`iex`

·      运行
`:eqc_install.install()`

如果一切顺利，你会看到：

`iex(1)> :eqc_install.install`
`Installation program for "Quviq QuickCheck Mini" version 2.01.0.`
`Installing in directory /usr/local/Cellar/erlang/18.1/lib/erlang/lib.`
`Installing ["eqc-2.01.0"].`
`Quviq QuickCheck Mini is installed successfully.`
`Bookmark the documentation at /usr/local/Cellar/erlang/18.1/lib/erlang/lib/eqc-2.01.0/doc/index.html.``:ok`
遵循有用的提示将文档添加到书签会是明智的选择。

11.1.2     在 Elixir 中使用 QuickCheck

现在你已经安装了 QuickCheck，我们回到了熟悉的领域。让我们创建一个新的项目来玩玩 QuickCheck：

`mix new quickcheck_playground`
打开 `mix.ex`，并添加以下内容：

清单 11.2 设置一个项目以使用 QuickCheck

```elixir
defmodule QuickcheckPlayground.Mixfile do
use Mix.Project

def project do
[app: :quickcheck_playground,
version: "0.0.1",
elixir: "~> 1.2-rc",
build_embedded: Mix.env == :prod,
start_permanent: Mix.env == :prod,
test_pattern: "*_{test,eqc}.exs",     #1
deps: deps]
end

def application do
[applications: [:logger]]
end

defp deps do
[{:eqc_ex, "~> 1.2.4"}]                #2
end
end
```
#1: 为测试指定测试模式。注意 QuickCheck 测试的后缀 “\_eqc”。

#2: 添加 Erlang QuickCheck 的 Elixir 包装器。

执行 `mix deps.get` 来获取依赖项。接下来让我们试一个例子！

列表反转 - QuickCheck 的 “Hello World”

我们将通过编写一个简单的列表反转属性来确保我们已经正确地设置了一切，即，反转一个列表两次会得到相同的列表。

```elixir
defmodule ListsEQC do
use ExUnit.Case
use EQC.ExUnit

property "reversing a list twice yields the original list" do
forall l <- list(int) do
ensure l |> Enum.reverse |> Enum.reverse == l
end
end
end
```
现在不用在意所有这些意味着什么。要运行这个测试，执行 `mix test test/lists_eqc.exs`：

`% mix test test/lists_eqc.exs`
`....................................................................................................`
`OK, passed 100 tests`
`.`

`Finished in 0.06 seconds (0.05s on load, 0.01s on tests)`
`1 test, 0 failures`
`Randomized with seed 704750`
太棒了！QuickCheck 刚刚运行了*一百*个测试。这是 QuickCheck 生成的默认测试数量。我们可以通过用 `@tag numtests: <N>` 进行注解来修改数量，其中 `<N>` 是一个正整数。让我们故意在属性中引入一个错误：

清单 11. 3. 这是一个错误的列表反转属性

```elixir
defmodule ListsEQC do
use ExUnit.Case
use EQC.ExUnit

property "reversing a list twice yields the original list" do
forall l <- list(int) do
# NOTE: THIS IS WRONG!
ensure l |> Enum.reverse == l
end
end
end
```
`ensure/2` 检查属性是否满足，并在属性失败时打印出一个错误消息。让我们再次运行 `mix test test/lists_eqc.exs` 看看会发生什么：

清单 11. 4 QuickCheck 检测到属性中的不一致，并报告一个失败的示例

`% mix test test/lists_eqc.exs`
`...................Failed! After 20 tests.`
`[0,-2]`
`not ensured: [-2, 0] == [0, -2]`
`Shrinking xxxx..x(2 times)`
`[0,1]`
`not ensured: [1, 0] == [0, 1]`

`1) test Property reversing a list twice gives back the original list (ListsEQC)`
`test/lists_eqc.exs:5`
`forall(l <- list(int)) do`
`ensure(l |> Enum.reverse() == l)`
`end`
`Failed for [0, 1]`

`stacktrace:`
`test/lists_eqc.exs:5`

`Finished in 0.1 seconds (0.05s on load, 0.06s on tests)``1 test, 1 failure`
经过 20 次尝试，QuickCheck 报告属性失败，并提供了一个*反例*来支持其声明。现在我们有信心我们已经正确地设置了 QuickCheck，我们可以进入好东西。但首先，你如何设计你自己的属性呢？

### 11.1.3     设计属性的模式

设计属性是基于属性的测试中最棘手的部分。但不用害怕！这里有一些指针在设计你自己的属性时会很有帮助。当你通过例子学习时，试着找出哪些启发式方法适合。

反函数

这是最容易利用的一种。一些函数也有一个反函数。

![](../../images/11_1.png)  

图 11. 1 反函数

图 11.1 说明了反函数的含义。主要的思想是反函数撤销了原函数的操作。因此，执行原函数后再执行反函数基本上什么都没做。我们可以利用这个属性来测试二进制的编码和解码，例如使用 `Base.encode64/1` 和 `Base.decode64!` 作为例子：

清单 11. 5 编码和解码是彼此的反函数

```elixir
property "encoding is the reverse of decoding" do
forall bin <- binary do
ensure bin |> Base.encode64 |> Base.decode64! == bin
end
end
```
你可以尝试执行上述属性，毫无意外，所有的测试都应该通过。这里有一些函数有反函数的更多例子：

·      编码和解码

·      序列化和反序列化

·      分割和连接

·      设置和获取

利用不变性

另一种技术是利用不变性。不变性是一个在应用特定转换时保持不变的属性。两个不变性的例子：

·      排序函数总是按顺序排序元素

·      单调递增函数总是前一个元素小于或等于下一个元素

假设我们想要测试一个排序函数。首先，我们创建一个辅助函数，检查一个列表是否按递增顺序排序：

```elixir
def is_sorted([]), do: true

def is_sorted(list) do
list
|> Enum.zip(tl(list))
|> Enum.all?(fn {x, y} -> x <= y end)
end
```
然后我们可以在属性中使用函数来检查排序函数是否正常工作：

清单 11.6 检查排序不变性的属性

```elixir
property "sorting works" do
forall l <- list(int) do
ensure l |> Enum.sort |> is_sorted == true
end
end
```
当你执行上述属性时，一切都应该通过。

使用现有的实现

假设你已经开发了一个可以在常数时间内进行排序的排序算法。测试你的实现的一个简单方法是与一个已知工作良好的*现有*实现进行比较。例如，我们可以用 *Erlang* 的一个来测试我们的自定义实现：

清单 11. 7 对现有实现进行测试是保持功能一致性的好方法

```elixir
property "List.super_sort/1" do
forall l <- list(int) do
ensure List.super_sort(l) == :lists.sort(l)
end
end
```

#### 使用更简单的实现

这是前一种技术的轻微变化。假设你想要测试一个Map的实现。一种方法是使用一个之前的map实现。然而，这可能太麻烦了，而且你的实现的每一个操作可能并不（原谅这个双关语）映射到你想要测试的实现。

还有另一种方法！与其使用一个map，为什么不使用像列表这样更简单的东西呢？是的，它可能不是世界上最高效的数据结构，但它简单，且易于创建map操作的实现。

![](../../images/11_2.png)  

图 11. 2 使用一个更简单的实现来测试一个已经测试过的实现

例如，让我们测试一下
`Map.put/3`
操作。当使用一个已存在的键添加一个值时，旧的值将被替换。我们如何测试这个呢？让一个例子告诉你：

清单 11. 8 使用一个更简单的实现来测试一个更复杂的实现

```elixir
property "storing keys and values" do
forall {k, v, m} <- {key, val, map} do
map_to_list = m |> Map.put(k, v) |> Map.to_list
map_to_list == map_store(k, v, map_to_list)
end
end

defp map_store(k, v, list) do
case find_index_with_key(k, list) do
{:match, index} ->
List.replace_at(list, index, {k, v})
_ ->
[{k, v} | list]
end
end

defp find_index_with_key(k, list) do
case Enum.find_index(list, fn({x,_}) -> x == k end) do
nil   -> :nomatch
index -> {:match, index}
end
end
```
`map_store/3`
辅助函数基本上模拟了如何
`Map.put/3`
会添加一个键/值对的行为。列表包含的元素是两元素元组。元组代表一个键/值对。当
`map_store/3`
找到匹配键的元组时，它将用相同的键但新的值替换整个元组。否则，新的键/值被插入到列表中。

在这里，我们正在利用一个事实，即一个map可以被表示为一个列表，而且
`Map.put/3`
的行为可以很容易地使用一个列表来实现。事实上，大多数操作都可以用上面介绍的类似技术来表示（并因此进行测试）。

执行不同顺序的操作

对于某些操作，顺序并不重要。这些例子有：

·      追加一个列表并反转它，与在列表前面添加一个元素并反转列表是一样的

·      以不同的顺序向集合中添加元素，不应影响集合中的结果元素

·      添加一个元素并排序，得到的结果与在元素前面添加一个元素并排序是一样的

清单 11.9 排序的最终结果总是相同的，无论元素在哪里被添加

```elixir
property "appending an element and sorting it is the same as prepending an element and sorting it" do
forall {i, l} <- {int, list} do
[i|l] |> Enum.sort == l ++ [i] |> Enum.sort
end
end
```
当你执行上述属性时，所有的测试都应该通过。

幂等操作

幂等操作是一种花哨的说法，意思是当一个操作执行一次或多次时，它将产生相同的结果。例如：

·      使用相同的谓词调用
`Enum.filter/2`
两次，与做一次是一样的

·      调用
`Enum.sort/1`
两次，与做一次是一样的

·      HTTP GET请求

另一个例子是
`Enum.uniq/2`, 其中调用函数两次不应有任何额外的效果：

清单 11.10 调用一个幂等函数一次或多次总是得到相同的结果

```elixir
property "calling Enum.uniq/1 twice has no effect" do
forall l <- list(int) do
ensure l |> Enum.uniq == l |> Enum.uniq |> Enum.uniq
end
end
```
运行这个属性将通过所有的测试。当然，这六个并不是唯一的，但它们是一个很好的起点。下一个拼图的部分是生成器。让我们直接开始吧。

11.1.4     生成器

生成器用于为我们的QuickCheck属性生成随机测试数据。这些数据可以是数字（整数，浮点数，实数等），字符串，甚至是不同种类的数据结构，如列表，元组和映射。

在本节中，我们将探索默认情况下可用的生成器。然后，我们将学习如何创建自己的自定义生成器。

11.1.5     内置生成器

QuickCheck预装了一堆生成器/生成器组合器。表11.1列出了你可能会遇到的一些更常见的：

| 生成器/组合器 | 描述 |
| --- | --- |
| `binary/0` | 生成随机大小的二进制。 |
| `binary/1` | 生成给定大小（以字节为单位）的二进制。 |
| `bool/0` | 生成一个随机布尔值。 |
| `char/0` | 生成一个随机字符。 |
| `choose/2` | 生成范围在M到N的数字。 |
| `elements/1` | 生成列表参数的一个元素。 |
| `frequency/1` | 在其参数中的生成器之间进行加权选择，使得选择每个生成器的概率与其配对的权重成正比。 |
| `list/1` | 生成由其参数生成的元素的列表。 |
| `map/2` | 生成一个映射，其中键由K生成，值由V生成。 |
| `nat/0` | 生成一个小的自然数（受生成大小的限制）。 |
| `non_empty/1` | 确保生成的值不为空。 |
| `oneof/1` | 使用列表生成器的随机选择的元素生成一个值。 |
| `orderedlist/1` | 生成由G生成的元素的有序列表。 |
| `real/0` | 生成一个实数。 |
| `sublist/1` | 生成给定列表的随机子列表。 |
| `utf8/0` | 生成一个随机utf8二进制。 |
| `vector/2` | 生成一个给定长度的列表，其中的元素由G生成。 |

表11.1 QuickCheck附带的生成器和生成器组合器的列表

你已经在前面的例子中看到了生成器的应用。以下是使用生成器的一些其他示例。

示例：指定列表的尾部

我们如何为获取列表的尾部编写规范呢？作为一个复习，这就是
`tl/1`
的作用：

清单 11.11 tl/1 获取列表的尾部

```elixir
iex> h tl
def tl(list)

返回一个列表的尾部。如果列表为空，则引发ArgumentError。

示例

┃ iex> tl([1, 2, 3, :go])``┃ [2, 3, :go]
```
非空列表的表示形式是
`[head|tail]`，其中
`head`
是列表的第一个元素，`tail`
是一个不包含头部的较小列表。有了这个定义，我们就可以定义属性了：

清单 11.12 获取列表尾部的属性

```elixir
property "tail of list" do
forall l <- list(int) do
[_head|tail] = l
ensure tl(l) == tail
end
end
```
让我们试试看会发生什么。

```elixir
1) test Property tail of list (ListsEQC)
test/lists_eqc.exs:11
forall(l <- list(int)) do
[_ | tail] = l
ensure(tl(l) == tail)
end
Failed for []
```
哎呀！原来，QuickCheck找到了一个反例——空列表！这正好，因为如果你回头看看
`tl/1`的定义，它会在列表为空时引发
`ArgumentError`。换句话说，我们应该纠正我们的属性。

我们可以尝试使用
`implies/1`
为我们的属性添加一个前提条件。这里的前提条件将始终确保生成的列表为空。让我们设置前提条件，我们只想要*非空*的列表：

清单 11.13 使用 implies/2 设置生成列表的前提条件

```elixir
property "tail of list" do
forall l <- list(int) do
implies l != [] do
[_head|tail] = l
ensure tl(l) == tail
end
end
end
```
这次当我们运行测试时，所有的测试都通过了，但我们看到了一些稍微不同的东西：

`xxxxxxxxxx.xxxxx.xx...x...x...xxx.xx..x....x.........x....x.............x..x........................(x10)...(x1)xxxxx`
`OK, passed 100 tests`
交叉符号（`x`）表示一些测试已经被丢弃，因为这些测试没有通过后置条件。理想情况下，你不希望测试用例被丢弃。我们可以用不同的方式表达，确保我们生成的列表总是非空的。在QuickCheck中，我们可以很容易地添加一个生成器组合器，因此摆脱
`implies/1`：

清单 11.14 使用 non\_empty/1 明确生成非空列表

```elixir
property "tail of list" do
forall l <- non_empty(list(int)) do
[_head|tail] = l
ensure tl(l) == tail
end
end
```
这次，*没有*测试用例被丢弃：

`.................................................................................................... OK, passed 100 tests`
示例：指定列表连接

到目前为止，我们只使用了一个生成器。有时候，这是不够的。假设我们想要测试
`Enum.concat/2`。一个直接的方法是测试
`Enum.concat/2`
对比内置的
`++`
操作符，它们做的事情是一样的。这需要两个列表：

清单 11.15 使用多个生成器

```elixir
property "list concatenation" do
forall {l1, l2} <- {list(int), list(int)} do
ensure Enum.concat(l1, l2) == l1 ++ l2
end
end
```
在下一节中，我们将看到如何定义我们自己的自定义生成器。你会发现QuickCheck足够表达，可以产生我们需要的任何类型的数据。

11.1.6     创建自定义生成器

我们一直在使用的所有生成器都是内置的。然而，我们同样可以轻松地创建自己的生成器。为什么要费这个劲呢？有时候，你希望QuickCheck生成的随机数据具有某些特性。

示例：指定字符串分割

假设我们想要测试
`String.split/2`。这个函数接受一个字符串和一个分隔符，并根据分隔符分割字符串。例如：

```elixir
iex(1)> String.split("everything|is|awesome|!", "|")
["everything", "is", "awesome", "!"]
```
退后一步，思考一下我们可能如何为
`String.split/2`编写一个属性。一种方法是测试字符串的*逆向*。给定一个函数
`f(x)`
和它的*逆向*，
`f-1(x)`，那么我们可以说：

![](../../images/11_F1.png)  

这意味着，当你对一个值应用一个函数，然后对结果值应用逆函数，你会得到原始值。

在这种情况下，使用分隔符分割字符串的逆操作是*连接*分割的结果和相同的分隔符。为此，我们编写了一个快速的辅助函数join，它接受分割操作的标记化结果和分隔符：

```elixir
def join(parts, delimiter) do
parts |> Enum.intersperse([delimiter]) |> Enum.join
end
```
这是一个例子：

```elixir
iex> join(["everything", "is", "awesome", !], [?|])
"everything|is|awesome|!"
```
有了这个，我们就可以为
`String.split/2`编写一个属性：

清单 11. 16 使用相同的分隔符分割和连接字符串是逆操作

```elixir
defmodule StringEQC do
use ExUnit.Case
use EQC.ExUnit

property "splitting a string with a delimiter and joining it again yields the same string" do
forall s <- list(char) do
s = to_string(s)
ensure String.split(s, ",") |> join(",") == s
end
end

defp join(parts, delimiter) do
parts |> Enum.intersperse([delimiter]) |> Enum.join
end
end
```
`to\_string`
在字符列表上

注意使用
`to\_string/1`。这个函数用于将参数转换为字符串，根据
`String.Chars`
*协议*。本书没有涉及协议，但关键是我们必须将字符列表转换为
`String.split/2`
可以理解的格式。

然而，有一个小问题。QuickCheck实际上生成包含逗号的字符串的概率是多少呢？让我们用
`collect/2`
来找出答案：

清单 11. 17 使用 collect/2，我们可以看到生成数据的分布

```elixir
property "splitting a string with a delimiter and joining it again yields the same string" do
forall s <- list(char) do
s = to_string(s)
collect string: s, in:                           #1
ensure String.split(s, ",") |> join(",") == s  #1
end
end
```
#1: `collect`
宏报告生成数据的统计信息

这是
`collect/2`
输出的一部分：

`1% <<"Ã‚Â¡N?Ã‚Â½W.E">>`
`1% <<121,6,53,194,189,5>>`
`1% <<"x2AÃ‚Â¤">>`
`1% <<"q$">>`
`1% <<"g">>`
`1% <<102,7,112>>`
`1% <<"f">>`
`1% <<98,75,6,194,154>>``1% <<"\\Ã‚Â¯\e">>`
即使你检查整个生成的数据集，你也很难找到包含逗号的东西。到底有多难呢？QuickCheck有
`classify/3`
可以解决这个问题：

清单 11.18 classify/3 对生成的数据运行一个布尔函数

```elixir
property "splitting a string with a delimiter and joining it again yields the same string" do
forall s <- list(char) do
s = to_string(s)
:eqc.classify(String.contains?(s, ","),
:string_with_commas,
ensure String.split(s, ",") |> join(",") == s)
end
end
```
`classify/3`
对生成的字符串输入和属性运行一个布尔函数，并显示结果。在这种情况下，它报告：

`....................................................................................................`
`OK, passed 100 tests`
`1% string_with_commas`
虽然所有的测试都通过了，但只有微不足道的*一百分之一*的数据有逗号。由于我们只有一百个测试，所以只有*一个*生成的字符串有一个或多个逗号。

我们真正想要的是生成*更多*包含*更多*逗号的字符串。幸运的是，QuickCheck给了我们这样做的工具。最终的结果是能够表达这样的属性，其中
`string_with_commas`
是我们接下来要实现的自定义生成器。

```elixir
property "splitting a string with a delimiter and joining it again yields the same string" do
forall s <- string_with_commas do
s = to_string(s)
ensure(String.split(s, ",") |> join(",") == s)
end
end
```
示例：生成包含逗号的字符串

让我们为我们的列表提出一些要求。

1.  它的长度必须在1到10个字符之间
2.  字符串应该包含小写字母
3.  字符串应该包含逗号
4.  逗号应该比字母出现得少

让我们解决列表中的第一件事。当使用
`list/1`
生成器时，我们无法控制列表的长度。为此，我们必须使用
`vector/2`
生成器，它接受一个长度和一个生成器。

在
`lib`中创建一个新文件
`eqc_gen.ex`。让我们从我们的第一个自定义生成器开始：

清单 11. 19 vector/2 生成指定长度的列表

```elixir
defmodule EQCGen do
use EQC.ExUnit

def string_with_fixed_length(len) do
vector(len, char)
end
end
```
然后用
`iex -S mix`打开一个
`iex`
会话。我们可以用
`:eqc_gen.sample/1`获取QuickCheck可能生成的样本：

`iex> :eqc_gen.sample(EQCGen.string_with_fixed_length(5))`
这是一个可能的输出：

`[170,246,255,153,8]`
`"ñísJ£"`
`"×¾sûÛ"`
`"ÈÚwä\t"`
`[85,183,155,222,83]`
`[158,49,169,40,2]`
`"¥Ùêr¿"`
`[58,51,129,71,177]`
`"æ¿q5º"``"C°{Sð"`

字符串表示

请记住，字符串在内部是字符列表，字符可以用整数表示。

生成固定长度的字符串并不好玩。有了
`choose/2`，我们可以引入一些变化。

清单 11.20 choose/2 返回一个随机数，我们可以在 vector/2 中使用它来生成不同长度的列表

```elixir
def string_with_variable_length do
let len <- choose(1, 10) do
vector(len, char)
end
end
```
这里使用
`let/2`
很重要。
`let/2`
将生成的值绑定用于另一个生成器。换句话说，这*不会*起作用：

清单 11.21 使用 choose/2 的错误方式。记住 choose/2 也是一个生成器。

```elixir
# 注意：这不起作用！
def string_with_variable_length do
vector(choose(1, 10), char)
end
```
那是因为vector/1的第一个参数应该是一个整数，而不是一个生成器。

提示：你不必重新启动 iex 会话

相反，你可以重新编译并重新加载指定模块的源文件。因此，在我们添加了新的生成器后，我们可以直接从会话中重新加载
`EQCGen`：

`iex(1)> r(EQCGen)`
`lib/eqc\_gen.ex:1: warning: redefining module EQCGen`
`{:reloaded, EQCGen, [EQCGen]}`

 尝试运行
`:eqc_gen.sample/1`
针对
`string_with_variable_length`：

`iex(1)> :eqc_gen.sample(EQCGen.string_with_variable_length)`
`"ß"`
`[188,220,86,82,6,14,230,136]`
`[150]`
`[65,136,250,131,106]`
`[4]`
`[205,6,254,43,64,115]`
`",ÄØ"`
`[184,203,190,93,158,29,250]`
`"vp\vwSçú"`
`[186,128,49]``[247,158,120,140,113,186]`
它有效！没有空列表，更长的列表中有十个元素。现在，来解决第二个要求：生成的字符串应该只包含小写字符。关键在于限制字符串中生成的值。目前，我们允许*任何*字符（包括UTF–8）成为字符串的一部分：

`vector(len, char)`
为了达到我们的目标，我们可以使用
`oneof/1`
生成器，它从生成器列表中随机选择一个元素。在这种情况下，我们只需要提供一个包含小写字母的单一列表。注意我们使用Erlang的
`:lists.seq/2`
函数来生成小写字母的序列：

`vector(len, oneof(:lists.seq(?a, ?z)))`
重新加载模块并再次运行
`eqc_gen.sample/1`：

`iex> :eqc_gen.sample(EQCGen.string_with_variable_length)`
我们得到了QuickCheck可能生成的一些样本：

`"kcra"`
`"iqtg"`
`"yqwmqusd"`
`"hoyacocy"`
`"jk"`
`"a"`
`"iekkoi"`
`"nugzrdgon"`
`"tcopskokv"`
`"wgddqmaq"``"lexsbkosce"`
很好！我们如何在生成的字符串中包含逗号呢？一种天真的方法是简单地将逗号字符作为生成的字符串的一部分：

`vector(len, oneof(:lists.seq(?a, ?z) ++ [?,]))`
这种方法的问题在于我们无法控制逗号出现的次数。我们可以使用
`frequency/1`来修复这个问题。在解释之前，先展示一下如何使用
`frequency/1`：

清单 11.22 使用 frequency/1 控制生成值的频率

`vector(len,frequency([{3, oneof(:lists.seq(?a, ?z))},`
`{1, ?,}]))`
当我们这样表达时，小写字母将被生成75%的时间，而逗号将被生成25%的时间。这是最终的结果：

清单 11.23 使用 frequency/1 增加生成的结果字符串中逗号的概率

```elixir
def string_with_commas do
let len <- choose(1, 10) do
vector(len, frequency([{3, oneof(:lists.seq(?a, ?z))},
{1, ?,}]))
end
end
end
```
重新加载模块并运行
`eqc_gen.sample/1`：

`iex> :eqc_gen.sample(EQCGen.string_with_commas)`
这是生成数据的一个样本：

`"acrn"`
`",,"`
`"uandbz,afl"`
`"o,,z"`
`",,wwkr"`
`",lm"`
`",h,s,aej,"`
`",mpih,vjsq"`
`"swz"`
`"n,,yc,"``"jlvmh,g"`
好多了！现在，让我们使用我们新铸造的生成器：

清单 11. 24 使用我们新的生成器，生成包含（更多）逗号的字符串

```elixir
property "splitting a string with a delimiter and joining it again yields the same string" do
forall s <- EGCGen.string_with_commas do # 1
s = to_string(s)
:eqc.classify(String.contains?(s, ","),
:string_with_commas,
ensure String.split(s, ",") |> join(",") == s)
end
end
```
#1 使用我们新的生成器

这次，结果*好多了*：

`....................................................................................................`
`OK, passed 100 tests`
`65% string_with_commas`
当然，如果你对测试数据的分布仍然不满意，你总是有权力自己调整值。检查测试数据的分布总是一种好习惯，特别是当你的数据依赖于某些特性，比如至少有一个逗号。以下是一些你可以尝试实现的生成器示例：

·      DNA序列。DNA序列只包含A、T、G和C。例如：
`ACGTGGTCTTAA`。

·      十六进制序列。十六进制包括0到9，以及字母
`A`
到
`F`。例如：
`0FF1CE`
和
`CAFEBEEF`。

·      排序且唯一的数字序列。例如：
`-4, 10, 12, 35, 100`。

11.1.7     递归生成器

让我们尝试一些*稍微*更具挑战性的事情。假设我们需要生成*递归*的测试数据。一个例子是JSON，其中JSON键的值可能是另一个JSON结构。另一个例子是树数据结构（我们将在下一节中看到）。

这就是我们需要*递归*生成器的时候。顾名思义，这些生成器会调用自己。在这个例子中，假设我们要为`List.flatten/1`编写一个属性，并且我们需要生成嵌套列表。

然而，当使用递归解决问题时，你必须注意不要有无限递归。防止这种情况的方法是让递归调用的输入在每次调用时都变得*更小*，并且以某种方式达到一个终止条件。

在QuickCheck中处理递归生成器的标准方法是使用`sized/2`。`sized/2`让你可以访问当前正在生成的测试数据的大小参数。我们可以使用这个参数来控制递归调用的输入大小。

示例：生成任意嵌套的列表（使用List.flatten/2测试）

举个例子。首先，我们将为我们的测试创建一个入口，以使用嵌套列表生成器：

清单 11.25 sized/2 给我们提供了生成数据的大小参数的访问

```elixir
defmodule EQCGen do
use EQC.ExUnit

def nested_list(gen) do
sized size do
nested_list(size, gen)
end
end

# nested_list/2 还未实现
end
```
`nested_list/1`接受一个生成器作为参数，并将其传递给`sized/2`中的`nested_list/2`。`nested_list/2`接受两个参数。`size`是由`gen`生成的当前测试数据的大小，而第二个参数是生成器。

我们现在需要实现`nested_list/2`。对于列表，有两种情况。列表要么是空的，要么不是。如果传入的大小为零，则应返回一个空列表：

清单 11. 26 实现 nested\_list/2 的空列表情况

```elixir
defmodule EQCGen do
use EQC.ExUnit

# nested/1 在这里

defp nested_list(0, _gen) do
[]
end
end
```
第二种情况是发生动作的地方：

清单 11. 27 实现 nested\_list/2 的非空列表情况。这里是递归发生的地方。

```elixir
defmodule EQCGen do
use EQC.ExUnit

# nested/1 在这里

# nested/2 空情况在这里

defp nested_list(n, gen) do
oneof [[gen|nested_list(n-1, gen)],
[nested_list(n-1, gen)]]
end
end
```
让我们用

`iex(1)> :eqc_gen.sample EQCGen.nested_list(:eqc_gen.int)`
试试看。这是结果：

`[[-10,[-7,[9,[4,[[]]]]]]]`
`[10,0,2,-3,[[-6,[[-2,-1]]]]]`
`[[8,[[11,[-7,-3,-9,10,-8,-10]]]]]`
`[5,8,[-10,-11,[7,[-4,-10,0,[5]]]]]`
`[[-8,-4,2,12,-6,9,1,[[[12,-4,[]]]]]]`
`[8,[4,12,[13,-12,[12,4,[15,14,[4]]]]]]`
`[[[[6,[-11,[[-6,[[[[[[-16]]]]]]]]]]]]]`
`[-7,13,[15,-13,[-3,[5,0,[16,-17,[[[[]]]]]]]]]`
`[18,[[[[[-8,-8,[3,[-12,[18,[13,[[]]]]]]]]]]]]`
`[[-2,[[[-6,-17,3,[[-18,[[12,[[[13,1]]]]]]]]]]]]`
`[[[[-15,[-17,[[[-16,[[[20,[[[17,10,[]]]]]]]]]]]]]]]``:ok`
万岁！我们成功地生成了一堆嵌套的整数列表。但你有没有注意到生成过程花费了*很长*的时间？问题出在这一行：

`oneof [[gen|nested_list(n-1, gen)],`
`[nested_list(n-1, gen)]]`
发生的事情是，尽管我们说选择*要么*
`[gen|nested_list(n-1, gen)]`
要么
`[nested_list(n-1, gen)]`。实际上发生的是，即使我们只需要其中一个，*两个*表达式都被评估了。我们需要的是使用*惰性求值*。懒惰只评估我们需要的`oneof/1`的部分。

幸运的是，我们只需要在 `oneof/1` 周围包裹一个 `lazy/1`：

```elixir
lazy do
oneof [[gen|nested_list(n-1, gen)],
[nested_list(n-1, gen)]]
end
```
这是最终版本：

```elixir
defmodule EQCGen do
use EQC.ExUnit

def nested_list(gen) do
sized size do
nested_list(size, gen)
end
end

defp nested_list(0, _gen) do
[]
end

defp nested_list(n, gen) do
lazy do
oneof [[gen|nested_list(n-1, gen)],
[nested_list(n-1, gen)]]
end
end
end
```
这次，嵌套列表的生成速度飞快。为了让概念深入人心，我们将通过另一个例子。

示例：生成平衡树

在这个例子中，我们将学习如何构建一个生成*平衡树*的生成器。作为复习，平衡树的特点是：

· 左右子树的高度相差最多为一

· 左右子树都是平衡的

和以前一样，我们首先创建入口点：

```elixir
defmodule EQCGen do
use EQC.ExUnit

def balanced_tree(gen) do
sized size do
balanced_tree(size, gen)
end
end

# balanced_tree/2 not implemented yet
end
```
树的终端节点是*叶节点*。这是树构造的基本情况：

```elixir
defmodule EQCGen do
use EQC.ExUnit

# balanced_tree/1 goes here

def balanced_tree(0, gen) do
{:leaf, gen}
end
end
```
注意我们用 `:leaf` 原子标记叶节点。接下来，我们需要实现节点*不是*叶子的情况：

```elixir
defmodule EQCGen do
use EQC.ExUnit

# balanced_tree/1 goes here

# balanced_tree/2 leaf node case here

def balanced_tree(n, gen) do
lazy do
{:node,
gen,
balanced_tree(div(n, 2), gen), # 1
balanced_tree(div(n, 2), gen)} # 1
end
end
end
```
#1: 每次递归调用都会将子树的大小减半

对于非叶节点，我们用 `:node` 标记元组，然后是生成器的值。最后，我们递归调用 `balanced_tree/2` 两次：一次是左子树，一次是右子树。每次递归调用都会将生成的子树的大小*减半*。这确保我们最终会达到基本情况并终止。

最后，我们用 `lazy/1` 包裹递归调用，以确保只在需要时调用递归调用。这是最终版本：

```elixir
defmodule EQCGen do
use EQC.ExUnit

def balanced_tree(gen) do
sized size do
balanced_tree(size, gen)
end
end

def balanced_tree(0, gen) do
{:leaf, gen}
end

def balanced_tree(n, gen) do
lazy do
{:node,
gen,
balanced_tree(div(n, 2), gen),
balanced_tree(div(n, 2), gen)}
end
end
end
```
我们可以生成一些带有整数生成器的平衡树：

```elixir
iex> :eqc_gen.sample EQCGen.balanced_tree(:eqc_gen.int)
```
这会给我们一个像这样的输出：

```elixir
{node,0,
{node,8,
{node,8,{node,8,{leaf,6},{leaf,-3}},{node,1,{leaf,5},{leaf,-7}}},
{node,1,{node,-4,{leaf,8},{leaf,3}},{node,1,{leaf,-8},{leaf,7}}}},
{node,-4,
{node,6,{node,-1,{leaf,6},{leaf,10}},{node,5,{leaf,-6},{leaf,-3}}},{node,-4,{node,6,{leaf,3},{leaf,-1}},{node,2,{leaf,8},{leaf,8}}}}}
```
尝试生成这些递归结构：

- 不平衡的树
- JSON

11.1.8 QuickCheck总结

QuickCheck的核心思想是编写你的代码的属性，并将测试用例的生成和属性的验证交给工具。一旦你提出了属性，工具就会处理剩下的部分，并可以轻松地生成数百到数千个测试用例。

另一方面，这并非都是彩虹和独角兽——你需要自己思考属性。虽然思考属性确实需要你花费大量的思考，但收益是巨大的。通常，通过属性的思考过程会让你对代码有更深入的理解。

我们已经介绍了足够的基础知识，使你能够编写自己的QuickCheck属性和生成器。还有其他我们没有探索的（高级）领域，比如测试数据的缩小和状态机的验证。我会在本章的最后温和地指向一些资源。现在，我们来看看一个名字颇具野心的工具Concuerror的并发测试。

11.2 Concuerror并发测试

虽然Elixir中的actor并发模型消除了一整类的并发错误，但它绝不是银弹。引入并发错误仍然非常可能（而且非常容易）。在接下来的例子中，我挑战你只通过肉眼查看代码就找出并发错误。

通过传统的单元测试暴露并发错误也是非常困难的，如果不是完全不足的努力。Concuerror是一个系统地清除并发错误的工具。虽然它不能找到每一种并发错误，但它能揭示的错误是非常令人印象深刻的。

我们将学习如何使用Concuerror并利用其能力来揭示难以发现的并发错误。我保证你会对结果感到惊讶。首先，我们需要安装Concuerror。

11.2.1 安装Concuerror

安装Concuerror很简单。以下是所需的步骤：

```bash
$ git clone https://github.com/parapluu/Concuerror.git
$ cd Concuerror
$ make
MKDIR ebin
GEN  src/concuerror_version.hrl
DEPS src/concuerror_callback.erl
ERLC src/concuerror_callback.erl
…
GEN  concuerror
```
输出的最后一行是Concuerror程序（一个Erlang脚本），为了方便，你可能希望将其包含到你的`PATH`中。

将`concuerror`添加到你的`PATH`

在Unix系统中，这意味着添加一行像这样的内容：

```bash
export PATH=$PATH:"/path/to/Concuerror"
```

11.2.2 设置项目

创建一个新项目：

```bash
mix new concuerror_playground
```
接下来，打开 `mix.exs` 并确保你添加了粗体的行：

```elixir
defmodule ConcuerrorPlayground.Mixfile do
use Mix.Project

def project do
[app: :concuerror_playground,
version: "0.0.1",
elixir: "~> 1.2-rc",
build_embedded: Mix.env == :prod,
start_permanent: Mix.env == :prod,
elixir_paths: elixirc_paths(Mix.env), #1
test_pattern: "*_test.ex*",           #1
warn_test_pattern: nil,               #1
deps: deps]
end

def application do
[applications: [:logger]]
end

defp deps do
[]
end

defp elixirc_paths(:test), do: ["lib", "test/concurrency"] #1
defp elixirc_paths(_),     do: ["lib"]                     #1
end
```
#1 这些行是为了让Concuerror测试得以编译。

默认情况下，Elixir测试以 `.exs` 结尾。这意味着它们没有被编译。Concuerror不理解 `.exs` 文件（甚至 `.ex` 文件），因此，我们需要告诉Elixir将这些文件编译成 `.beam`。为了实现这一点，我们首先修改测试模式以接受 `.ex` 和 `.exs` 文件。我们还关闭了 `warn_test_pattern` 选项，该选项在 `test` 目录中有 `.ex` 文件时会发出警告。

最后，我们添加两个 `elixirc_path/1` 函数并添加 `elixir_paths` 选项。这明确地告诉编译器我们希望将 `lib` 和 `test/concurrency` 中的文件都编译。

在我们继续看示例之前，还有最后一点。Concuerror能够以有用的图表显示其输出。我们稍后会看到几个例子。

输出是一个Graphviz `.dot` 文件。Graphviz是一个开源的图形可视化软件。它可以通过大多数包管理器或者通过<http://www.graphviz.org/>获取。确保Graphviz已经正确安装：

```bash
% dot -V dot - graphviz version 2.38.0 (20140413.2041)
```
11.2.3 Concuerror能检测的错误类型

Concuerror是如何施展其魔力的呢？该工具对你的代码（通常以测试的形式）进行插桩，并知道哪些点可以进行进程交错。有了这个知识，它就可以系统地搜索并报告它能找到的任何错误。它可以检测到的一些与并发相关的错误包括：

- 死锁
- 竞态条件
- 意外的进程崩溃

在接下来的例子中，我们将看到Concuerror能够挑选出的错误类型。

11.2.4 死锁

当两个操作都在等待对方完成，因此都无法进行时，就会发生死锁。当Concuerror发现一个程序状态，其中一个或多个进程被阻塞在 `receive` 上，并且没有其他进程可用于调度时，它会认为该状态已经死锁。我们将看到两个这样的死锁例子。

示例：Ping Pong（通信死锁）

我们从一个简单的例子开始。在 `lib` 中创建 `ping_pong.ex`：

```elixir
defmodule PingPong do

def ping do
receive do
:pong -> :ok
end
end

def pong(ping_pid) do
send(ping_pid, :pong)
receive do
:ping -> :ok
end
end
end
```
在 `test/concurrency` 中创建一个对应的测试文件，命名为 `ping_pong_test.ex`。让我们看看测试：

```elixir
Code.require_file "../test_helper.exs", __DIR__

defmodule PingPong.ConcurrencyTest do
import PingPong

def test do
ping_pid = spawn(fn -> ping end)
spawn(fn -> pong(ping_pid) end)
end
end
```
测试本身非常简单。我们生成两个进程，一个运行 `ping/0` 函数，一个运行 `pong/1` 函数。`pong` 函数接收 `ping` 进程的pid。

与ExUnit测试相比，有一些细微的差别。再次注意，与我们通常的以 `.exs` 结尾的测试文件不同，我们通过Concuerror的并发测试需要被编译，因此必须以 `.ex` 结尾。此外，测试函数本身被命名为 `test/0`。

你稍后会看到，Concuerror期望测试函数*没有元数*（没有参数）。此外，如果你没有明确提供测试函数名，它会自动寻找 `test/0`。运行测试稍微复杂一些。首先，我们需要编译测试：

```bash
% mix test
```
接下来，我们需要运行Concuerror。我们需要明确告诉Concuerror在哪里找到Elixir、ExUnit以及我们项目的编译后的二进制文件。我们通过指定路径（`--pa`）并指向相应的 `ebin` 目录来做到这一点：

```bash
concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin/ \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.PingPong.ConcurrencyTest \
--graph ping_pong.dot \--show_races true
```
然后我们需要告诉Concuerror确切的模块，使用 `-m` 标志。我们需要说 `Elixir.PingPong.ConcurrencyTest` 而不仅仅是 `PingPong.ConcurrencyTest`。`--graph` 告诉Concuerror生成Graphviz的输出可视化，`--show_races true` 告诉Concuerror突出显示竞态条件。

此外，这里还有一个 `-t` 选项。这个 `-t` 选项和一个值一起告诉Concuerror要执行的测试函数。如前所述，它默认查找 `test/0`。如果你想指定自己的测试函数，那么你需要提供 `-t` 和相应的测试函数名。看看那！Concuerror找到了一个错误：

```bash
# ... output omitted
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)Summary: 1 errors, 1/1 interleaving explored
```
这是 `concuerror_report.txt` 的输出：

```bash
Erroneous interleaving 1:
* Blocked at a 'receive' (when all other processes have exited):
P.2 in ping_pong.ex line 11
--------------------------------------------------------------------------------

Interleaving info:
1: P: P.1 = erlang:spawn(erlang, apply, [#Fun<'Elixir.PingPong.ConcurrencyTest'.'-test/0-fun-0-'.0>,[]])
in erlang.erl line 2497
2: P: P.2 = erlang:spawn(erlang, apply, [#Fun<'Elixir.PingPong.ConcurrencyTest'.'-test/0-fun-1-'.0>,[]])
in erlang.erl line 2497
3: P: exits normally
4: P.2: pong = erlang:send(P.1, pong)
in ping_pong.ex line 10
5: Message (pong) from P.2 reaches P.1
6: P.1: receives message (pong)
in ping_pong.ex line 4
7: P.1: exits normally

Done! (Exit status: warning)Summary: 1 errors, 1/1 interleaving explored
```
你可能会想知道 `P`、`P.1` 和 `P.2` 是什么。`P` 是父进程。`P.1` 是父进程生成的第一个进程，`P.2` 是父进程生成的第二个进程。现在，让我们告诉Concuerror生成交错的可视化：

```bash
% dot -Tpng ping_pong.dot > ping_pong.png
```
`ping_pong.png` 看起来像这样：

![](../../images/11_3.png)

图 11. 3 Concuerror显示我们一个被阻塞的进程

报告上的编号行对应图像上的数字。同时查看图像和报告有助于拼凑出导致问题的事件。这就像玩侦探游戏，拼凑犯罪现场的线索！这次，犯罪现场是一个GenServer程序。

示例：GenServer在另一个同步调用中对自身进行同步调用

OTP行为可以保护我们免受许多潜在的并发错误，但是很可能会自食其果。下一个例子展示了如何做到这一点。换句话说，不要在家里尝试这个：

```elixir
defmodule Stacky do
use GenServer
require Integer

@name __MODULE__

def start_link do
GenServer.start_link(__MODULE__, :ok, name: @name)
end

def add(item) do
GenServer.call(@name, {:add, item})
end

def tag(item) do
GenServer.call(@name, {:tag, item})
end

def stop do
GenServer.call(@name, :stop)
end

def init(:ok) do
{:ok, []}
end

def handle_call({:add, item}, _from, state) do
new_state = [item|state]
{:reply, {:ok, new_state}, new_state}
end

def handle_call({:tag, item}, _from, state) when Integer.is_even(item) do
add({:even, item})
end

def handle_call({:tag, item}, _from, state) when Integer.is_odd(item) do
add({:odd, item})
end

def handle_call(:stop, _from, state) do
{:stop, :normal, state}
end
end
```
数字被添加到Stack GenServer中。如果数字是偶数，那么一个标记的元组 `{:even, number}` 将被添加到堆栈中。如果是奇数，那么 `{:odd, number}` 将被推入堆栈。这是*预期的*行为（再次强调，这与当前的实现不符）：

```elixir
iex(1)> Stacky.start_link
{:ok, #PID<0.87.0>}

iex(2)> Stacky.add(1)
{:ok, [1]}

iex(3)> Stacky.add(2)
{:ok, [2, 1]}

iex(4)> Stacky.add(3)
{:ok, [3, 2, 1]}

iex(5)> Stacky.tag(4)
{:ok, [{:even, 4], 3, 2, 1]}

iex(6)> Stacky.tag(5){:ok, [{:odd, 5}, {:even, 4], 3, 2, 1]}
```
不幸的是，当我们尝试 `Stack.tag/1` 时，我们得到了一个令人讨厌的错误消息：

```bash
16:44:26.939 [error] GenServer Stacky terminating
** (stop) exited in: GenServer.call(Stacky, {:add, {:even, 4}}, 5000)
** (EXIT) time out
(elixir) lib/gen_server.ex:564: GenServer.call/3
(stdlib) gen_server.erl:629: :gen_server.try_handle_call/4
(stdlib) gen_server.erl:661: :gen_server.handle_msg/5
(stdlib) proc_lib.erl:240: :proc_lib.init_p_do_apply/3
Last message: {:tag, 3}State: [3, 2, 1]
```
花一点时间看看你能否找出问题。在你思考的时候，让Concuerror帮你一点。在 `test/concurrency` 中创建 `stacky_test.ex`。测试很简单：

```elixir
Code.require_file "../test_helper.exs", __DIR__

defmodule Stacky.ConcurrencyTest do

def test do
{:ok, _pid} = Stacky.start_link
Stacky.tag(1)
Stacky.stop
end
end
```
运行 `mix test`，然后运行Concuerror看看会发生什么：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.Stacky.ConcurrencyTest \--graph stacky.dot
```
这是输出：

```bash
# output truncated ...
Tip: A process crashed with reason '{timeout, ...}'. This may happen when a call to a gen_server (or similar) does not receive a reply within some standard timeout. Use the '--after_timeout' option to treat after clauses that exceed some threshold as 'impossible'.
Tip: An abnormal exit signal was sent to a process. This is probably the worst thing that can happen race-wise, as any other side-effecting operation races with the arrival of the signal. If the test produces too many interleavings consider refactoring your code.
Info: You can see pairs of racing instructions (in the report and --graph) with '--show_races true'
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)Summary: 1 errors, 1/2 interleavings explored
```

阅读Concuerror的输出是非常重要的。部分原因是因为Concuerror可能需要你的帮助来进行错误检测。需要注意的是*提示*。让我们从第一个开始：

```bash
Tip: A process crashed with reason '{timeout, ...}'. This may happen when a call to a gen_server (or similar) does not receive a reply within some standard timeout. Use the '--after_timeout' option to treat after clauses that exceed some threshold as 'impossible'.
```
Concuerror总是假设 `after` 子句是*可能*达到的。因此，它会搜索那些会触发该子句的交错。然而，由于添加到堆栈是一个相当简单的操作，我们可以明确地告诉Concuerror说 `after` 子句永远不会被触发，使用 `--after_timeout N` 标志，其中任何高于 `N` 的值都被视为 `:infinity`。让我们再次运行Concuerror，使用 `--after_timeout 1000` 标志：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.Stacky.ConcurrencyTest \
--graph stacky.dot \--after_timeout 1000
```
有趣的是，这次没有发出更多的提示。然而，如前所述，Concuerror已经发现了一个错误：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.Stacky.ConcurrencyTest \
--graph stacky.dot \--after_timeout 1000

# ... output truncated
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)
Summary: 1 errors, 1/1 interleavings explored
# ... output truncated
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)Summary: 1 errors, 1/1 interleavings explored
```
报告揭示了一些关于它找到的错误的细节：

```bash
Erroneous interleaving 1:
* Blocked at a 'receive' (when all other processes have exited):
P in gen.erl line 168P.1 in gen.erl line 168
```
`Blocked at a 'receive'` 基本上是Concuerror告诉你发生了死锁。

接下来，它显示了如何发现错误的详细信息：

```bash
Interleaving info:
1: P: undefined = erlang:whereis('Elixir.Stacky')
in gen.erl line 298
2: P: [] = erlang:process_info(P, registered_name)
in proc_lib.erl line 678
3: P: P.1 = erlang:spawn_opt({proc_lib,init_p,[P,[],gen,init_it,[gen_server,P,P,{local,'Elixir.Stacky'},'Elixir.Stacky',ok,[]]],[link]})
in erlang.erl line 2673
4: P.1: undefined = erlang:put('$ancestors', [P])
in proc_lib.erl line 234
5: P.1: undefined = erlang:put('$initial_call', {'Elixir.Stacky',init,1})
in proc_lib.erl line 235
6: P.1: true = erlang:register('Elixir.Stacky', P.1)
in gen.erl line 301
7: P.1: {ack,P.1,{ok,P.1}} = P ! {ack,P.1,{ok,P.1}}
in proc_lib.erl line 378
8: Message ({ack,P.1,{ok,P.1}}) from P.1 reaches P
9: P: receives message ({ack,P.1,{ok,P.1}})
in proc_lib.erl line 334
10: P: P.1 = erlang:whereis('Elixir.Stacky')
in gen.erl line 256
11: P: #Ref<0.0.1.188> = erlang:monitor(process, P.1)
in gen.erl line 155
12: P: {'$gen_call',{P,#Ref<0.0.1.188>},{tag,1}} = erlang:send(P.1, {'$gen_call',{P,#Ref<0.0.1.188>},{tag,1}}, [noconnect])
in gen.erl line 166
13: Message ({'$gen_call',{P,#Ref<0.0.1.188>},{tag,1}}) from P reaches P.1
14: P.1: receives message ({'$gen_call',{P,#Ref<0.0.1.188>},{tag,1}})
in gen_server.erl line 382
15: P.1: P.1 = erlang:whereis('Elixir.Stacky')
in gen.erl line 256
16: P.1: #Ref<0.0.1.209> = erlang:monitor(process, P.1)
in gen.erl line 155
17: P.1: {'$gen_call',{P.1,#Ref<0.0.1.209>},{add,{odd,1}}} = erlang:send(P.1, {'$gen_call',{P.1,#Ref<0.0.1.209>},{add,{odd,1}}}, [noconnect])in gen.erl line 166
```
最后一行告诉我们导致死锁的行：

```bash
17: P.1: {'$gen_call',{P.1,#Ref<0.0.1.209>},{add,{odd,1}}} = erlang:send(P.1, {'$gen_call',{P.1,#Ref<0.0.1.209>},{add,{odd,1}}}, [noconnect])
in gen.erl line 166
```
这里的问题是，当两个或更多的同步调用相互等待时，你会得到一个死锁。在这个例子中，同步函数 `tag/1` 的回调调用了 `add/1`，而 `add/1` 本身也是同步的。`tag/1` 会在 `add/1` 返回时返回，但 `add/1` 也在等待 `tag/1` 返回。因此，两个进程都处于死锁状态。

既然我们知道问题出在哪里，那就让我们修复它。需要改变的只是 `tag/1` 回调函数：

```elixir
defmodule Stacky do

# ...

def handle_call({:tag, item}, _from, state) when Integer.is_even(item) do
new_state = [{:even, item} |state]
{:reply, {:ok, new_state}, new_state}
end

def handle_call({:tag, item}, _from, state) when Integer.is_odd(item) do
new_state = [{:odd, item} |state]
{:reply, {:ok, new_state}, new_state}
end

# ...end
```
记得编译然后再次运行Concuerror：

```bash
# ... output omitted
Tip: An abnormal exit signal was sent to a process. This is probably the worst thing that can happen race-wise, as any other side-effecting operation races with the arrival of the signal. If the test produces too many interleavings consider refactoring your code.
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)Summary: 1 errors, 1/1 interleavings explored
```
哎呀！Concuerror报告了另一个错误。出了什么问题？让我们再次打开报告看看：

```bash
Erroneous interleaving 1:
* At step 30 process P exited abnormally
Reason:
{normal,{'Elixir.GenServer',call,['Elixir.Stacky',stop,5000]}}
Stacktrace:
[{'Elixir.GenServer',call,3,[{file,"lib/gen_server.ex"},{line,564}]},
{'Elixir.Stacky.ConcurrencyTest',test,0,[{file,"test/concurrency/stacky_test.ex"},{line,8}]}]
```
提示指出了一个异常退出。然而从外表看，我们的GenServer*正常*退出，而 `Stacky.stop/0` 导致了这个。既然这是Concuerror不应该担心的事情，我们可以安全地告诉它，进程以 `:normal` 作为原因退出是可以的，使用 `--treat_as_normal normal` 选项：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.Stacky.ConcurrencyTest \
--graph stacky.dot \
--show_races true  
--after_timeout 1000 \
--treat_as_normal normal

# ... some output omitted
Warning: Some abnormal exit reasons were treated as normal (--treat_as_normal).
Tip: An abnormal exit signal was sent to a process. This is probably the worst thing that can happen race-wise, as any other side-effecting operation races with the arrival of the signal. If the test produces too many interleavings consider refactoring your code.
Done! (Exit status: completed)Summary: 0 errors, 1/1 interleavings explored
```
万岁！现在一切都好了！

示例：进程注册的竞态条件

创建 `lib/spawn_reg.ex`。这个例子将演示由进程注册引起的竞态条件。如果你记得，进程注册基本上就是给一个进程分配一个名字。看看下面的实现，看你能否发现竞态条件。

```elixir
defmodule SpawnReg do

@name __MODULE__

def start do
case Process.whereis(@name) do
nil ->
pid = spawn(fn -> loop end)
Process.register(pid, @name)
:ok
_ ->
:already_started
end
end

def loop do
receive do
:stop ->
:ok
_ ->
loop
end
end
end
```
这个程序看起来足够无辜。`start/0` 函数创建了一个命名的进程，但在此之前，它会检查是否已经用该名字注册过。当生成时，进程在接收到 `:stop` 消息时终止，并在其他情况下继续愉快地运行。你能找出这个程序的问题吗？

在 `test/concurrency_test/spawn_reg_test.ex` 中创建测试文件。我们在另一个进程中生成 `SpawnReg` 进程，然后我们告诉 `SpawnReg` 进程停止：

```elixir
Code.require_file "../test_helper.exs", __DIR__

defmodule SpawnReg.ConcurrencyTest do

def test do
spawn(fn -> SpawnReg.start end)
send(SpawnReg, :stop)
end
end
```
Concuerror发现了一个问题（记得先做一个 `mix test`）：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.SpawnReg.ConcurrencyTest \
--graph spawn_reg.dot

# ... output omitted
Info: You can see pairs of racing instructions (in the report and --graph) with '--show_races true'
Error: Stop testing on first error. (Check '-h keep_going').

Done! (Exit status: warning)Summary: 1 errors, 1/2 interleavings explored
```
它还告诉我们使用 `--show_races true` 来揭示竞争指令的对。让我们这样做：

```bash
% concuerror --pa /usr/local/Cellar/elixir/HEAD/lib/elixir/ebin \
--pa /usr/local/Cellar/elixir/HEAD/lib/ex_unit/ebin \
--pa _build/test/lib/concuerror_playground/ebin     \
-m Elixir.SpawnReg.ConcurrencyTest \
--graph spawn_reg.dot \--show_races true
```
让我们检查一下错误交错的报告：

```bash
Erroneous interleaving 1:
* At step 3 process P exited abnormally
Reason:
{badarg,[{erlang,send,
['Elixir.SpawnReg',stop],
[9,{file,"test/concurrency/spawn_reg_test.ex"}]}]}
Stacktrace:
[{erlang,send,
['Elixir.SpawnReg',stop],
[9,{file,"test/concurrency/spawn_reg_test.ex"}]}]
* Blocked at a 'receive' (when all other processes have exited):P.1.1 in spawn_reg.ex line 17
```
它告诉我们，在第三步，`SpawnReg.stop/0` 调用失败，原因是 `:badarg`。`P.1.1` 进程也被死锁了。换句话说，它从未收到它正在等待的消息。
`P.1.1` 是什么进程？这是由父进程生成的第一个进程生成的第一个进程。用更少的话来说：

```elixir
spawn(fn -> SpawnReg.start end)
```
Concuerror可能会这样说的另一个原因是我们没有“拆除”我们的进程。一般来说，对于Concuerror测试，一旦我们完成了进程，让它们退出是一种好的做法，比如发送 `:stop` 消息。如果我们检查交错信息，我们可以更好地理解问题：

```bash
Interleaving info:
1: P: P.1 = erlang:spawn(erlang, apply, [#Fun<'Elixir.SpawnReg.ConcurrencyTest'.'-test/0-fun-0-'.0>,[]])
in erlang.erl line 2495
2: P: Exception badarg raised by: erlang:send('Elixir.SpawnReg', stop)
in spawn_reg_test.ex line 9
3: P: exits abnormally ({badarg,[{erlang,send,['Elixir.SpawnReg',stop],[9,{file,[116,101,115,116,47,99,111,110|...]}]}]})
4: P.1: undefined = erlang:whereis('Elixir.SpawnReg')
in process.ex line 359
5: P.1: P.1.1 = erlang:spawn(erlang, apply, [#Fun<'Elixir.SpawnReg'.'-start/0-fun-0-'.0>,[]])
in erlang.erl line 2495
6: P.1: true = erlang:register('Elixir.SpawnReg', P.1.1)
in process.ex line 338
7: P.1: exits normally
--------------------------------------------------------------------------------

Pairs of racing instructions:
*    2: P: Exception badarg raised by: erlang:send('Elixir.SpawnReg', stop)6: P.1: true = erlang:register('Elixir.SpawnReg', P.1.1)
```
Concuerror已经帮助我们发现了一个竞态条件！事实上，它甚至指出了导致这个问题的竞争指令对！你可能会发现图像更有帮助。你还会注意到，图像中包含了一个指向竞争指令对的错误。非常方便！

这是图形版本：

![](../../images/11_4.png)

图 11.4 Concuerror显示一个竞态条件

这里的竞态条件发生是因为进程可能还没有完成设置名字。因此，如果 `:name` 还没有注册，`send/2` 可能会失败。Concuerror已经确定这是一个*可能*的交错。如果你在控制台中尝试这个，你很可能甚至没有遇到错误。

11.3       Concuerror的总结

我们刚刚看到了Concuerror可以挑选出的一些并发错误。许多这样的错误并不明显，有时甚至令人惊讶。使用传统的单元测试技术，几乎不可能暴露出Concuerror相对容易捕获的并发错误。此外，单元测试工具无法产生导致错误的进程追踪，无论是进程死锁、崩溃还是竞态条件。Concuerror是我在开发Elixir程序时会密切关注的一个工具。

11.4       资源

这两个工具都是由研究产生的，因此，你最有可能看到的是关于QuickCheck和Concuerror这样的工具的论文，而不是书籍。你正在见证对后者的一次谦逊的尝试。幸运的是，近年来，这两个工具的创建者们已经在会议上进行了演讲和研讨会，这些都可以在网上免费获取。如果你想深入了解QuickCheck和Concuerror，以下是一些你会发现有用的资源：

- Software Testing with QuickCheck (John Hughes的论文)
- Testing Erlang Data Types with Quviq QuickCheck (Thomas Arts, Laura M. Castro和John Hughes的论文)
- Jesper Louis Anderson有一系列优秀的文章[[5]](#uGplayAVlyLaX4IyOPPBFu5)，他在这些文章中开发了一个QuickCheck模型，用来测试Erlang 18.0中Map的新实现。
- 使用Concuerror进行并发程序的测试驱动开发 (Alkis Gotovos, Maria Christakis和Konstantinos Sangonas的论文)

在本章中，我们看到了两个强大的工具。一个能够生成你想要的尽可能多的测试用例，另一个能够寻找难以发现的并发错误，并可能揭示我们代码中的洞察。总结一下，我们已经学习了：

- 如何在Elixir中使用QuickCheck和Concuerror（尽管它们最初是为Erlang程序设计的）
- 如何通过指定比特定单元测试更一般的属性来使用QuickCheck生成测试用例
- 学习一些指针来提出我们自己的属性
- 设计自定义生成器来产生我们需要的确切数据
- 使用Concuerror来检测各种并发错误，如通信死锁、进程死锁和竞态条件
- 看到了一些并发错误可能发生的例子

我们还没有探索所有的特性，一些高级但非常有用的特性被遗漏了。感谢上帝，否则我永远也写不完这本书！然而，本章应该给你提供了进行自己的探索所需要的基础知识和工具。

[****[1]****](#uEandRAdHEMbKa7scWKaW7C) http://krestenkrab.github.io/triq

[****[2]****](#uY3Qeh8W6N7zl8IWhUktnSA) https://github.com/manopapad/proper

[****[3]****](#ud7Cx2vjA84I2jInhUdGBw8) http://www.quviq.com/downloads/

[****[4]****](#u635lIFw7sxq7be8l3pcDE6) 这是一个可以给你的朋友留下深刻印象并烦扰你的同事的优秀词汇。

[****[5]****](#uwnx7uBuXSXwJ6LEmLvJuxF) https://medium.com/@jlouis666