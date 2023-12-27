# 第10章 Dialyzer和类型规范

本章内容包括：

- 什么是Dialyzer以及它是如何工作的
- 使用Dialyzer发现代码中的不一致
- 编写类型规范和定义自己的类型

根据你的倾向，类型的提及可能会让你欣喜若狂或者退避三舍。作为一种动态类型语言，Elixir免除了你在代码库中大量使用类型的需求，这一点类似于Haskell。有人可能会认为这导致了更快的开发周期。然而，Elixir程序员不应该过于自满。静态类型语言可以在*编译*时捕捉到一整类错误，而动态语言只能在*运行时*捕捉到这些错误。

幸运的是，语言中内置的容错功能试图拯救我们自己。没有这些功能的语言（Ruby，我在看你）将会直接崩溃。然而，我们有责任尽可能地使我们的软件可靠。在本章中，我们将学习如何利用类型来实现这一点。

我们将了解Dialyzer，这是一个与Erlang发行版捆绑在一起的工具。这个强大的工具用于消除某些类别的软件错误。最棒的部分是，你不需要对你的代码做任何特别的处理。

你将了解一些关于Dialyzer背后有趣的理论。这将帮助你解读它的（有时是隐晦的）错误信息。你还将理解为什么Dialyzer不是解决所有类型问题的灵丹妙药。

在本章的最后部分，我们将学习如何通过在代码中添加类型，使Dialyzer更好地寻找错误。在本章结束时，你将学会如何将Dialyzer作为开发工作流的一部分。

Dialyzer的命名者因为这个与电信相关的缩写而值得加薪。Dialyzer代表了Erlang的不一致性分析器。Dialyzer是一个帮助你发现代码中不一致之处的工具。具体是什么类型的不一致呢？以下是一个列表：

- 类型错误
- 引发异常的代码
- 无法满足的条件
- 冗余代码
- 竞态条件

我们将很快亲自看到Dialyzer是如何发现这些不一致的。在此之前，了解Dialyzer的内部工作原理是有帮助的。

10.1       Dialyzer是如何工作的

静态语言可以在编译时捕捉潜在的错误。动态语言的本质意味着它们只能在运行时检测到这些错误。Dialyzer试图将静态类型检查器的一些优点带给像Elixir/Erlang这样的动态语言。

Dialyzer的主要目标之一是不干扰现有程序。这意味着不应该期望任何Erlang（和Elixir）程序员重写代码来适应Dialyzer。

这导致了一个非常好的结果：你不需要提供给Dialyzer任何额外的信息，它就能完成它的工作。这并不是说你*不能*这样做。事实上，正如你稍后将看到的，你可以提供额外的类型信息，让Dialyzer在寻找不一致时做得更好。

10.2       成功类型

Dialyzer使用*成功类型*的概念来收集和推断类型信息。了解Dialyzer

如何工作是值得的。要理解成功类型是什么，我们需要了解一点关于Elixir类型系统的知识。

像Elixir这样的动态语言需要一个比静态类型系统更宽松的类型系统，因为函数可能会接受多种类型的参数。

例如，让我们看看布尔“和”函数。在像Haskell这样的静态语言中，`and`函数可以这样实现：

`and :: Bool -> Bool -> Bool`
`and x y | x == True && y == True = True | otherwise = False`
第一行
`and :: Bool -> Bool -> Bool`
是函数的类型签名。它表明
`and`
是一个接受两个布尔值作为参数并返回一个布尔值的函数。如果类型检查器看到任何非布尔值作为输入到
`and`，你的程序将无法通过编译。Elixir版本会是什么样子呢？

清单 10.1 在Elixir中实现的布尔与运算

`defmodule MyBoolean do`

`def and(true, true) do`
`true`
`end`

`def and(false, _) do`
`false`
`end`

`def and(_, false) do`
`false`
`end`
`end`
多亏了模式匹配，我们可以将
`and/2`
表示为三个函数子句。什么是对
`and/2`的有效参数？第一和第二个参数接受
`true`,
`false`和
`_`，
而返回值都是布尔值。

正如你已经知道的，“\_”意味着“任何东西”。因此，以下是对
`and/2`的完全合理的调用：

`MyBoolean.and(false, "great success!")`
`MyBoolean.and([1, 2, 3], false)`
Haskell类型检查器不会允许像前面展示的Elixir程序，因为它不允许将“任何东西”作为一种类型。它无法处理这种不确定性。

另一方面，Dialyzer采用了一种不同的类型推断算法，称为成功类型。成功类型非常乐观。它总是假设你的所有函数都被正确使用。因此，你的代码在被证明有罪之前是无辜的。

成功类型从*过度估计*你的函数的有效输入和输出开始。所以它从假设你的函数可以接受任何东西并返回任何东西开始。然而，随着它更好地理解你的代码，它会生成*约束*。这些约束反过来将限制输入值，因此，输出。

例如，如果它看到
`x + y`，那么
`x`
和
`y`
肯定是数字。像
`is_atom(z)`
这样的守卫也提供了额外的约束。一旦生成了约束，就是解决它们的时候了，就像解谜一样。谜题的解答就是函数的成功类型。相反，如果没有找到解决方案，约束是*不可满足的*，你手头就有一个类型违规。

然而，重要的是要意识到，因为Dialyzer总是假设你的代码是正确的，所以它*不*保证你的代码是类型安全的。现在，在你起身离开房间之前，由此产生了一个非常好的属性。如果Dialyzer发现了什么问题，那么它*肯定*是对的。所以Dialyzer的第一课是这样的：

Dialyzer永远不会出错！

`Dialyzer 在它说你的代码有问题时，总是\*始终\*正确的。`

这就是为什么当Dialyzer表示你的代码有问题时，它是100%正确的。更严格的类型检查器从假设你的代码是错误的开始，你的代码必须成功通过类型检查才能允许编译。这也意味着你的代码（或多或少）被保证是类型安全的。

所以再次强调：Dialyzer *不会*（或永远不会）发现所有类型违规。然而，如果它发现了问题，那么你的代码*肯定*存在问题。现在我们对成功类型（success typings）的工作方式有了一些背景知识，让我们转向了解Elixir中的类型。

10.3 揭示Elixir中的类型，第一部分

我们一直在使用Elixir，但并没有太多强调确切的类型。在本节和下一节中，我们将稍微更加关注这一点。

从Elixir 1.2开始，有一个非常方便的工具在`iex`中可以打印给定数据类型的信息，称为`i/1`。例如，`"ohai"`和`'ohai'`之间有什么区别（注意分别使用双引号和单引号）？让我们来找出答案：

清单 10.2 使用i/1揭示Elixir字符串的类型

```elixir
iex> i("ohai")
Term
"ohai"
数据类型
BitString
字节大小
4
描述
这是一个字符串：一个UTF-8编码的二进制文件。它被双引号包围打印，因为其中的所有UTF-8码点都是可打印的。
原始表示
<<111, 104, 97, 105>>
参考模块String, :binary
```
现在让我们对比一下`'ohai'`：

清单 10.3 使用i/1揭示字符列表的类型

```elixir
iex> i('ohai')
Term
'ohai'
数据类型
List
描述
这是一个打印为一系列码点的整数列表，用单引号分隔，因为其中的所有整数都代表有效的ascii字符。按照惯例，这样的整数列表被称为“字符列表”。
原始表示
[111, 104, 97, 105]
参考模块List
```
下次如果你遇到类型错误并感到困惑，立即使用`i/1`工具。

10.4 开始使用Dialyzer

Dialyzer可以使用Erlang源代码或调试编译的BEAM字节码。显然，这让我们只能选择后者。这意味着在我们运行Dialyzer之前，必须记得先执行`mix compile`。

记得先编译！

自从开始使用Dialyzer以来，我已经忘记了多少次这个步骤。幸运的是，一旦我发现了Dialyxir（稍后你会看到），我就不再需要手动编译我的代码了。

Dialyzer随Erlang发行版安装，并且存在作为命令行程序：

```shell
% dialyzer
```
检查PLT /Users/benjamintan/.dialyzer_plt是否最新...
dialyzer: 未找到PLT: /Users/benjamintan/.dialyzer_plt
使用选项：
--build_plt   构建新的PLT；或
--add_to_plt  添加到现有的PLT

例如，使用以下命令：
dialyzer --build_plt --apps erts kernel stdlib mnesia
注意，构建如上所述的PLT可能需要20分钟左右

如果您后来需要其他应用程序的信息，比如crypto，
您可以通过以下命令扩展PLT：
dialyzer --add_to_plt --apps crypto
对于不在Erlang/OTP中的应用程序，请使用绝对文件名。

太好了，我们已经确信Dialyzer确实已安装。但是这个*PLT*是什么，Dialyzer正在尝试搜索什么呢？

10.4.1 PLT：持久查找表

PLT代表持久查找表（Persistent Lookup Table）。Dialyzer使用PLT来存储其分析结果。您还可以使用之前构建的PLT作为Dialyzer的起点。这变得很重要，因为任何非平凡的Elixir应用程序可能都会涉及OTP。如果我们对这样的应用程序运行Dialyzer，分析无疑会花费很长时间。

由于OTP库不会改变，我们总是可以构

建一个“基础PLT”，只在我们的应用程序上运行Dialyzer，相比之下将会花费更短的时间。这的另一面是，一旦您升级了Erlang和/或Elixir，您必须记得重建PLT。

### 10.4.2 Dialyxir（Dialyxir）

传统上，运行 Dialyzer 需要输入相当多的命令。幸好，由于程序员的懒惰，现在有一些库包含了 `mix` 任务，使我们的生活更加轻松。我们将使用的一个库是 *Dialyxir*。Dialyxir 包含了 `mix` 任务，使得在 Elixir 项目中使用 Dialyzer 成为一种乐趣。

Dialyxir 可以作为依赖安装（我们稍后会看到），也可以全局安装。我们首先全局安装 Dialyxir，以便构建 PLT 表。这不是绝对必要的，但当你不想将 Dialyxir 安装为项目依赖时，这是很有用的：

```elixir
git clone https://github.com/jeremyjh/dialyxir
cd dialyxir
mix archive.build
mix archive.install
```
让我们开始使用 Dialyxir 吧！

### 10.4.3 构建 PLT 表（建立 PLT 表）

如前所述，我们首先需要构建 PLT。令人高兴的是，Dialyxir 有一个 mix 任务用于构建 PLT：

```elixir
% mix dialyzer.plt
```
准备好咖啡，因为这需要一段时间：

```
Starting PLT Core Build ... this will take awhile
dialyzer --output_plt /Users/benjamintan/.dialyxir_core_18_1.2.0-rc.1.plt --build_plt --apps erts kernel stdlib crypto public_key -r /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../eex/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../elixir/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../ex_unit/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../iex/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../mix/ebin
...
cover:compile_beam_directory/1
cover:modules/0
cover:start/0
fprof:analyse/1
fprof:apply/3
fprof:profile/1
httpc:request/5
httpc:set_options/2
inets:start/2
inets:stop/2
leex:file/2
yecc:file/2
Unknown types:
compile:option/0
done in 2m33.16s
done (passed successfully)
```
只要 PLT 构建成功，你就不必担心“未知类型”和其他警告。

### 10.5 Dialyzer 可以检测的软件差异（Dialyzer 能检测的软件问题）

在本节中，我们将创建一个项目来进行实验。示例项目是一个简单的货币转换器，只能将新加坡元转换为美元。创建项目：

```elixir
% mix new dialyzer_playground
```
打开 `mix.exs` 并添加 Dialyxir：

#### 清单 10.4 添加 dialyxir 依赖 (mix.exs)

```elixir
defmodule DialyzerPlayground.Mixfile do
# ...

  defp deps do
    [{:dialyxir, "~> 0.3", only: [:dev]}]
  end
end
```
像往常一样，记得运行 `mix deps.get`。现在乐趣开始了！

### 10.5.1 捕捉类型错误（捕获类型错误）

我们从一个简单的示例开始，演示 Dialyzer 如何捕捉简单的类型错误。创建 `lib/bug_1.ex`：

#### 清单 10.5 Cashy.Bug1 有一个类型错误。你能发现吗？(lib/bug_1.ex)

```elixir
defmodule Cashy.Bug1 do

  def convert(:sgd, :usd, amount) do
    {:ok, amount * 0.70}
  end

  def run do
    convert(:sg

d, :usd, :one_million_dollars)
  end
end
```
`convert/3` 函数接受三个参数。前两个参数 *必须* 是原子 `:sgd` 和 `:usd`。`amount` 被假定为一个数字，并用来计算从新加坡元到美元的汇率。相当直接的东西。

现在想象一下 `run/1` 函数可能存在于另一个模块中。不难想象有人错误地使用这个函数，比如将原子作为 `convert/3` 的最后一个参数，而不是数字。

只有当 `run/1` 被执行时，代码的问题才会显现。否则，这个问题甚至可能不会浮现。值得注意的是，静态类型语言永远不会允许这样的代码。对我们来说幸运的是，我们有 Dialyzer！让我们运行 Dialyzer 看看会发生什么：

```elixir
% mix dialyzer
```
这是输出：

```
% mix dialyzer
Compiled lib/bug_1.ex
Generated dialyzer_playground app
...
Proceeding with analysis...
bug_1.ex:7: Function run/0 has no local return
bug_1.ex:8: The call 'Elixir.Cashy.Bug1':convert('sgd','usd','one_million_dollars') will never return since it differs in the 3rd argument from the success typing arguments: ('sgd','usd',number())
done in 0m1.00s
done (warnings were emitted)
```
Dialyzer 发现了一个问题！Dialyzer 说的“无本地返回”意味着该函数肯定会失败。这通常意味着 Dialyzer 发现了一个类型错误，因此确定该函数永远不会返回。

正如它正确指出的，`convert/3` 因为我们给它的参数会导致 `ArithmeticError` 而永远不会返回。

### 10.5.2 错误使用内置函数

让我们检查另一种情况。创建文件 `lib/bug_2.ex`：

清单 10.6 Cashy.Bug2 中错误使用了内置函数。（lib/bug\_2.ex）

```elixir
defmodule Cashy.Bug2 do

def convert(:sgd, :usd, amount) do
{:ok, amount * 0.70}
end

def convert(_, _, _) do
{:error, :invalid_amount}
end

def run(amount) do
case convert(:sgd, :usd, amount) do
{:ok, amount} ->
IO.puts "converted amount is #{amount}"

{:error, reason} ->
IO.puts "whoops, #{String.to_atom(reason)}"
end
end
end
```

第一个函数子句与 `Cashy.Bug1` 中的完全相同。此外，还有一个捕获所有情况的子句，返回 `{:error, :invalid_amount}`。再次想象 `run/1` 被某处客户端代码调用。你能发现问题所在吗？让我们看看 Dialyzer 的说法：

```
% mix dialyzer
...
bug_2.ex:18: 调用 erlang:binary_to_atom(reason@1::'invalid_amount','utf8') 违反了约定 (Binary,Encoding) -> atom() 当 is_subtype(Binary,binary()), is_subtype(Encoding,'latin1' | 'unicode' | 'utf8')
执行完毕耗时 0m1.02s（发出了警告）
```

有趣！这里似乎有一个问题：

`erlang:binary_to_atom(reason@1::'invalid_amount','utf8')`

似乎违反了某种形式的合约。在第18行，正如 Dialyzer 所指出的，我们调用了 `String.to_atom/1`。看来这是问题的原因。`erlang:binary_to_atom/2` 正在寻找的合约是：

`(Binary,Encoding) -> atom()`

我们提供的输入是 `'invalid_amount' 和 'utf8'`，转换成 `(Atom, Encoding)`。仔细检查后，我们应该调用 `Atom.to_string/1` 而不是 `String.to_atom/1`。哎呀。

### 10.5.3 冗余代码

冗余代码阻碍了可维护性。在某些情况下，Dialyzer 可以分析代码路径并发现冗余代码。`lib/bug_3.ex` 提供了这方面的一个例子：

清单 10.7 Cashy.Bug3 中有一个冗余的代码路径。（lib/bug\_3.ex）

```elixir
defmodule Cashy.Bug3 do

def convert(:sgd, :usd, amount) when amount > 0 do
{:ok, amount * 0.70}
end

def run(amount) do
case convert(:sgd, :usd, amount) do
amount when amount <= 0 ->
IO.puts "whoops, should be more than zero"
_ ->
IO.puts "converted amount is #{amount}"
end
end
end
```

这次，我们在 `convert/3` 中添加了一个保护子句，确保只有在 `amount` 大于零时才进行货币转换。现在看看 `run/1`。它有两个子句。其中一个处理 `amount` 小于或等于零的情况。第二个子句处理 `amount` 更大的情况。Dialyzer 对此有何看法？

```
% mix dialyzer
...
bug_3.ex:9: Guard test amount@2::{'ok',float()} =< 0 永远不会成功
执行完毕耗时 0m0.97s（发出了警告）
```

Dialyzer 已经帮助我们识别了一些冗余代码！由于我们在 `convert/3` 中有了保护子句，我们可以确定 `amount <= 0` 的情况永远不会发生。再次强调，这是一个简单的例子。然而，不难想象程序

员可能不了解这种行为，因此尝试覆盖所有情况，实际上这是冗余的。

### 10.5.4 保护子句中的类型错误

在使用保护子句的情况下可能会发生类型错误。保护子句限制了它们包裹的参数的类型。在下一个示例中，该参数是 `amount`。让我们看看 `lib/bug_4.ex`。你可能很容易发现问题所在：

清单 10.8 当 run/1 执行时会发生错误。你能猜出为什么吗？（lib/bug\_4.ex）

```elixir
defmodule Cashy.Bug4 do

def convert(:sgd, :usd, amount) when is_float(amount) do
{:ok, amount * 0.70}
end

def run do
convert(:sgd, :usd, 10)
end
end
```

让 Dialyzer 发挥作用：

```
% mix dialyzer
...
bug_4.ex:7: 函数 run/0 没有本地返回
bug_4.ex:8: 调用 'Elixir.Cashy.Bug4':convert('sgd','usd',10) 永远不会返回，因为它在第三个参数上与成功类型参数不符：('sgd','usd',float())
执行完毕耗时 0m0.97s（发出了警告）
```

如果我们足够仔细，我们会意识到 `10` 不是 `float()` 类型，因此不符合保护子句。关于保护子句的一个有趣之处在于，它们永远不会抛出异常，这正是它们的全部意义，因为你正在特别允许只有某些类型的输入。然而，这有时可能导致类似上面那种令人困惑的错误，当时看起来 `10` 应该被允许通过保护子句。

10.5.5     用一些间接方法让Dialyzer绊倒

在本节的最后一个例子中，我们看一下`Cashy.Bug1`的一个略微修改的版本。创建`lib/bug_5.ex`：

清单 10.9 Dialyzer将无法捕获此错误。 (lib/bug\_5.ex)

```elixir
defmodule Cashy.Bug5 do

def convert(:sgd, :usd, amount) do
amount * 0.70
end

def amount({:value, value}) do
value
end

def run do
convert(:sgd, :usd, amount({:value, :one_million_dollars}))
end
end
```
现在，看起来很明显，Dialyzer很可能会报告与`Cashy.Bug1`相同的错误。注意，我们在这里只是通过使`amount/1`成为一个函数调用，返回我们想要转换的金额的实际值，从而增加了一层间接性。让我们测试一下我们的假设：

```shell
% mix dialyzer
...
Proceeding with analysis... done in 0m1.05s done (passed successfully)
```
等等，什么？不幸的是，在这种情况下，由于这种间接性，Dialyzer无法检测到这种差异。这是一个完美的过渡到下一个关于类型规范的主题。我们将在那之后回到`Cashy.Bug5`。

10.6       类型规范

我们已经提到，Dialyzer可以在没有你的帮助下愉快地运行。我们已经向你展示了一些Dialyzer可以从`Cashy.Bug1`到`Cashy.Bug4`检测到的软件差异的例子。

然而，正如`Cashy.Bug5`所示，一切并非都是彩虹和独角兽。虽然Dialyzer可能会报告`passed successfully`，但这并不意味着你的代码没有错误。有些情况下，Dialyzer无法完全自己检测到。

通过一些努力，我们可以帮助Dialyzer揭示难以检测的错误。我们通过添加*类型规范*，或者简称*Typespecs*来做到这一点。

将类型规范添加到你的代码的另一个优点是，它可以作为一种文档形式。特别是对于动态语言，有时候并不明显什么是有效的输入，以及返回值的类型。在本节中，你将学习如何编写你自己的类型规范，不仅为了编写更好的文档，而且为了编写更可靠的代码。

10.6.1 编写类型规范

最好的方式是通过一些例子来向你展示如何使用类型规范。定义类型规范的格式是：

`@spec function_name(type1, type2) :: return_type`
这个格式应该是不言自明的。我们稍后会讲解什么是有效的类型值（`type1`，`type2`和`return_type`）。下面是一些已经预定义的类型和类型联合（当你通过例子学习时，这些会更有意义）。这些并不是详尽无遗的，而只是可用类型的一个很好的样本。

| 类型 | 描述 |
| --- | --- |
| `term` | 这被定义为`any`。`term`代表任何有效的Elixir项，这也包括带有`_`作为参数的函数。 |
| `boolean` | 这被定义为两种布尔类型的联合 - `false | true`。`char`：这被定义为有效字符的范围：`0..0x10ffff`。注意`..`是范围操作符。 |
| `number` | 这被定义为整数和浮点数的联合 - `integer | float`。 |
| `binary` | 用这个表示Elixir字符串。 |
| `char_list` | 用这个表示Erlang字符串。这被定义为`[char]`。 |
| `list` | 这被定义为`[any]`。你总是可以约束列表的类型。例如，`[number]`。 |
| `fun` | `(... -> any)`表示*任何*匿名函数。你可能想要根据函数的元数和返回类型来约束这个。例如，`(() -> integer)`是一个返回整数的元数为零的匿名函数，而`(integer, atom -> [boolean])`是一个元数为二的函数，它分别接受一个整数和一个原子，并返回一个布尔值列表。 |
| `pid` | 进程id |
| `tuple` | 任何类型的元组。其他有效的选项是`{}`和`{:ok, binary}`。 |
| `map` | 任何类型的映射。其他有效的选项是`%{}`和`%{atom => binary}`。 |

表 10.1 一些可用于类型规范的类型

接下来的几个例子会让你有更好的感觉。

示例：加法

让我们从一个简单的加法函数开始，这个函数接受两个数字并返回另一个数字。这是一种可能的类型规范：

清单 10.10 add/2的一种可能的类型规范

```elixir
@spec add(integer, integer) :: integer
def add(x, y) do
x + y
end
```
就目前而言，`add/2`可能过于严格。我们可能还想包括浮点数*或*整数。写的方式如下：

清单 10.11 包括浮点数和整数作为输入参数和返回值

```elixir
@spec add(integer | float, integer | float) :: integer | float
def add(x, y) do
x + y
end
```
幸运的是，我们可以使用内置的简写类型`number`，它被定义为`integer | float`。`|`表示`number`是一个联合类型。顾名思义，联合类型是由两种或多种类型组成的类型。联合类型可以应用于输入类型和返回值的类型。

清单 10.12 使用number简写表示integer | float

```elixir
@spec add(number, number) :: number
def add(x, y) do
x + y
end
```
我们将在学习如何定义自己的类型时，很快看到更多的联合类型的例子。

示例：List.fold/3

让我们尝试解决一些更具挑战性的问题：`List.fold/3`。这个函数通过一个函数从左边减少给定的列表。它还需要一个累加器的初始值。这是函数的工作方式：

```elixir
iex> List.foldl([1, 2, 3], 10, fn (x, acc) -> x + acc end)
```
如预期，函数将返回`16`。第一个参数是列表，然后是累加器的初始值。最后一个参数是执行每一步减少的函数。这是函数签名（取自`List`源代码）：

清单 10.13 List.foldl的函数签名

```elixir
def foldl(list, acc, function)
when is_list(list) and is_function(function) do
# the implementation is not important here
end
```
`List.foldl/3`已经将`list`的类型限制为列表，这是由于`is_list/1`守卫子句。然而，列表的元素可以是任何有效的Elixir项。同样，`function`需要是一个实际的函数。`function`必须是二元的，其中第一个参数的类型与`elem`相同，第二个参数的类型与`acc`相同。最后，这个函数的返回结果应该与`acc`的类型相同。指定`List.foldl/3`的类型规范的一种可能的方式可能是：

清单 10.14 编写List.foldl/3类型规范的一种可能（但不是很有帮助）的方式

```elixir
@spec foldl([any], any, (any, any -> any)) :: any
def foldl(list, acc, function)
when is_list(list) and is_function(function) do
# the implementation is not important here
end
```
虽然从Dialyzer的角度来看，这个类型规范在技术上没有什么问题，但它并没有显示输入参数和返回值之间的类型关系。我们可以使用没有限制的类型变量作为函数的参数，如下所示：

`@spec function(arg) :: arg when arg: var`
注意`var`，它表示任何变量。因此，我们可以向类型规范提供更好的变量名，如下所示：

清单 10.15 在类型规范中提供更好的变量名

```elixir
@spec foldl([elem], acc, (elem, acc -> acc)) :: acc when
elem: var, acc: var
def foldl(list, acc, function)
when is_list(list) and is_function(function) do
# the implementation is not important here
end
```

示例：映射函数

我们也可以使用守卫来限制作为函数参数的类型变量，如下所示：

`@spec function(arg) :: arg when arg: atom`
在这个例子中，我们有自己的`Enum.map/2`实现。创建`lib/my_enum.ex`。注意单个参数和返回结果的类型规范。

清单 10.16 映射函数的类型规范 (lib/my\_enum.ex0

```elixir
defmodule MyEnum do

@spec map(f, list_1) :: list_2 when
f: ((a) -> b),
list_1: [a],
list_2: [b],
a: term,
b: term
def map(f, [h|t]), do: [f.(h)| map(f, t)]

def map(f, []) when is_function(f, 1), do: []
end
```
从类型规范中，我们声明：

- `f`（`map/2`的第一个参数）是一个单元函数，它接受一个项并返回另一个项。
- `list_1`（`map/2`的第二个参数）和`list_2`（`map/2`的返回结果）是项的列表。

我们也费了一番功夫来命名`f`的输入和输出类型。虽然这并不是严格必要的，但明确地放置`a`和`b`表示`f`在类型`a`上操作并返回类型`b`，并且`map/2`接受类型`a`的列表作为输入并输出类型`b`的列表。如你所见，类型规范可以传达很多信息。

10.7 编写你自己的类型

你可以使用`@type`定义你自己的类型。例如，让我们为RGB颜色代码创建一个自定义类型。创建`lib/hexy.ex`：

清单 10.17 使用@type定义自定义类型 (lib/hexy.ex)

```elixir
defmodule Hexy do
@type rgb() :: {0..255, 0..255, 0..255}           #1
@type hex() :: binary                            #2

@spec rgb_to_hex(rgb) :: hex                      #3
def rgb_to_hex({r, g, b}) do
[r, g, b]
|> Enum.map(fn x -> Integer.to_string(x, 16) |> String.rjust(2, ?0) end)
|> Enum.join
end
end
```
#1 RGB颜色代码的类型别名

#2 Hex颜色代码的类型别名

#3 在规范中使用自定义类型定义

我们本可以只指定`@spec rgb_to_hex(tuple) :: binary`，但这并不能传达很多信息，也不能对输入参数进行很多约束，除了说预期一个元组。在这种情况下，甚至一个空的元组都是可以接受的。

相反，我们指定了一个有三个元素的元组，并进一步指定每个元素都是范围在0到255的整数。最后，我们给类型一个描述性的名字，比如`rgb`。对于`hex`，我们没有简单地称之为`binary`（在Elixir中是一个字符串），而是将其别名为`hex`，以便更具描述性。

10.7.1 多重返回类型和无主体函数子句

函数由多个返回类型组成是很常见的。在这种情况下，我们可以使用*无主体函数子句*来将类型注解组合在一起。考虑以下情况：

清单 10.18 使用无主体函数子句并将类型规范附加到该子句上 (lib/hexy.ex)

```elixir
defmodule Hexy do
@type rgb() :: {0..255, 0..255, 0..255}
@type hex() :: binary

@spec rgb_to_hex(rgb) :: hex | {:error, :invalid}
def rgb_to_hex(rgb) #1

def rgb_to_hex({r, g, b}) do
[r, g, b]
|> Enum.map(fn x -> Integer.to_string(x, 16) |> String.rjust(2, ?0) end)
|> Enum.join
end

def rgb_to_hex(_) do
{:error, :invalid}
end
end
```
#1 无主体函数子句

这次，`rgb_to_hex/1`有两个子句。第二个子句是后备情况。这个后备情况总是会返回`{:error, :invalid}`。这意味着我们必须更新我们的类型规范。

我们可以创建一个*无主体*函数子句，而不是像我们在前一个例子中那样在第一个函数子句上面写它。需要注意的一点是我们如何定义子句。这样会起作用：

`def rgb_to_hex(rgb)`
而这样*不会*起作用：

`def rgb_to_hex({r, g, b})`
如果你试图编译文件，你会得到一个错误消息：

`** (CompileError) lib/hexy.ex:7: can use only variables and \\ as arguments of bodiless clause`
有一个无主体函数子句可以将所有可能的类型规范集中在一个地方，这样就可以避免在每个函数子句上都撒上类型规范。

### 10.7.2 揭示Elixir中的类型，第二部分

除了`i/1`，还有另一个方便的`iex`助手：`t/1`。`t/1`打印给定模块或给定函数/元数对的类型。如果你想了解模块中使用的类型（可能是自定义的）的更多信息，这很方便。例如，让我们研究一下在`Enum`中找到的类型：

```elixir
iex> t Enum
@type t() :: Enumerable.t()
@type element() :: any()
@type index() :: non_neg_integer()
@type default() :: any()
```
在这里，我们可以看到`Enum`有四个定义的类型。`Enumerable.t`看起来很有趣。`Enumerable`模块也有一堆定义的类型：

```elixir
iex> t Enumerable
@type acc() :: {:cont, term()} | {:halt, term()} | {:suspend, term()}
@type reducer() :: (term(), term() -> acc())
@type result() :: {:done, term()} | {:halted, term()} | {:suspended, term(), continuation()}
@type continuation() :: (acc() -> result())
@type t() :: term()
```
10.7.3 回到Bug #5

在本章结束之前，让我们如约回到`Cashy.Bug5`。没有任何类型规范，Dialyzer无法找到明显的错误。然而，现在让我们添加类型规范：

清单 10.19 添加类型规范到Cashy.Bug5 (lib/bug\_5.ex)

```elixir
defmodule Cashy.Bug5 do

@type currency() :: :sgd | :usd

@spec convert(currency, currency, number) :: number
def convert(:sgd, :usd, amount) do
amount * 0.70
end

@spec amount({:value, number}) :: number
def amount({:value, value}) do
value
end

def run do
convert(:sgd, :usd, amount({:value, :one_million_dollars}))
end
end
```
这次当我们运行Dialyzer时，它显示了一个我们*没有*预期的错误，以及一个我们之前预期但没有得到的错误：

```shell
bug_5.ex:22: The specification for 'Elixir.Cashy.Bug5':convert/3 states that the function might also return integer() but the inferred return is float()

bug_5.ex:32: Function run/0 has no local return
bug_5.ex:33: The call 'Elixir.Cashy.Bug5':amount({'value','one_million_dollars'}) breaks the contract ({'value',number()}) -> number()
done in 0m1.05s
done (warnings were emitted)
```
让我们先处理第二个，更直接的错误。由于我们传入的是一个原子（`:one_million_dollars`）而不是一个数字，Dialyzer正确地抱怨。

那么第二个错误呢？它说我们的类型规范表明函数可能会返回一个`integer`，但Dialyzer推断出的是函数只返回`float`。现在当我们检查函数的主体时，我们看到：

`amount * 0.70`
当然！与浮点数相乘总是会返回一个浮点数！这就是为什么Dialyzer会抱怨。这很好，因为Dialyzer能够在某些情况下检查我们的类型规范是否存在明显的错误。

10.8 练习

1. 尝试使用`Cashy.Bug1`到`Cashy.Bug5`，并尝试添加错误的类型规范。看看错误消息是否对你有意义。一个更难的练习是设计一个有明显错误的代码，但Dialyzer无法捕获这个错误。这是我们在`Cashy.Bug5`中做过的事情。

2. 想象你正在编写一个纸牌游戏。一张牌由花色和值组成。为牌、花色和牌的值提出类型。让你开始：

```elixir
@type card :: {suit(), value()} 
@type suit :: <FILL THIS IN> 
@type value :: <FILL THIS IN>
```
3. 尝试为一些内置函数指定类型。一个好的开始是`List`和`Enum`模块。一个好的灵感来源是Erlang/OTP（是的，Erlang！）的代码库。语法稍有不同，但不应该对你构成主要的障碍。

10.9 总结

Dialyzer已经在生产中得到了很好的效果。例如，它发现了OTP中以前未被发现的软件差异。虽然它不是银弹，但Dialyzer提供了一些静态类型检查器的优点，比如Haskell。

在你的函数中包含类型不仅可以作为文档，还可以让Dialyzer在发现差异时更准确。作为一个额外的好处，Dialyzer也可以指出你在类型规范中是否犯了错误。在本章中，我们学习了：

- 成功类型，Dialyzer使用的类型推断机制
- 如何使用Dialyzer并解释它有时难以理解的错误消息
- 通过提供类型规范和守卫，如`is_function(f, 1)`和`is_list(l)`，如何提高Dialyzer的准确性

在下一章中，我们将看一下为Erlang生态系统专门编写的测试工具。这些工具不是普通的单元测试工具。这些强大的工具可以根据你定义的一般属性生成测试用例，并找出并发错误。