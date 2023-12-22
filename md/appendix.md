# 附录A 安装Erlang和Elixir

欢迎来到第0章，或者出版商喜欢称之为附录*A*。我们将讲述如何尽快在您的系统上设置Elixir。我将覆盖Mac OS X、一些Linux发行版和MS Windows。按难易程度排序。

## A.1 获取Erlang

在安装Elixir之前，我们必须先安装Erlang。在撰写本文时，Erlang的最低版本是18.0。到目前为止，Elixir在跟进新的Erlang版本方面做得非常好。

就像获取Elixir有多种方式一样，Erlang也是如此。如果您可以通过包管理器获取它，那就这样做。否则，最不易出问题的方式（迄今为止！）是前往Erlang Solutions网站[[1]](#uGRexWD7e8DL2GrOrcFocH8)并下载副本。他们为几个Linux发行版（Ubuntu、CentOS、Debian、Fedora甚至是Raspberry Pi的一个版本）、Mac OS X和Windows托管Erlang包。

## A.2 方法1：包管理器/预构建安装程序。

如果您的操作系统自带，您应始终选择通过包管理器安装Elixir。这通常会在最短的时间内让您上手。以下部分概述了一些更受欢迎的操作系统的安装步骤。如果您的系统未列出，请不要担心。通常会有指令在网络空间中流传。

### A.2.1 通过Homebrew和Macports安装Mac OS X

您可能已经安装了Homebrew或Macports包管理器。如果是这样，那么您距离一个全新而闪亮的Elixir（和Erlang）安装只有一步之遥。对于Homebrew：

`% brew update && brew install elixir`
对于Macports，只需执行常规的`port install`：

`% sudo port install elixir`
注意，我们没有指定任何版本号。通过包管理器安装通常会安装最新的*稳定*版本。我们将在后面的部分讨论如何从源代码构建和安装Elixir。

### A.2.2 Linux（Ubuntu和Fedora）

由于有数十亿个Linux发行版，我将只限于更受欢迎的，即Ubuntu和Fedora。如果是这样，为您安装Elixir将是一行命令的事。

Fedora 17到22（及更高版本）

如果您使用的是Fedora 17或更新版本（并且早于Fedora 21）：

`% yum install elixir`
如果您使用的是Fedora 22或更高版本：

`% dnf install elixir`
Ubuntu

Ubuntu风味的发行版需要做更多的工作。您首先需要添加Erlang solutions仓库：

`% wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb && sudo dpkg -i erlang-solutions_1.0_all.deb`
接下来，所有Ubuntu用户都知道：

`% sudo apt-get update`
接下来，我们需要获取Erlang（和一系列其他Erlang相关应用程序）：

`% sudo apt-get install esl-erlang`
最后，我们可以获取Elixir：

`% sudo apt-get install elixir`
### A.2.3 MS Windows

在Windows上获取Elixir再简单不过了。您需要做的就是安装Elixir网络安装程序[[2]](#unSboXWaDHFFHWhG44f39C3)，您就可以设置好了。

## A.3 方法2：从头开始编译（仅限Linux/Unix）

所以，您觉得自己很幸运吗？有时，您会迫不及待地想尝试那些令人赞叹的功能。有时候，您可能想直接

尝试Elixir，甚至修复一个bug或实现一个新功能。如果是这样，那么这是您要走的路线。

幸运的是，Elixir唯一依赖的是Erlang。如果您已经正确安装了Erlang，那么从源代码编译Elixir通常不会太戏剧性。

在本节中，我假设您正在使用Unix/Linux系统，并且已安装所有必要的构建工具，例如`make`。首先，您需要从官方仓库克隆Elixir：

`% git clone https://github.com/elixir-lang/elixir.git`
接下来，切换到新创建的目录：

`% cd elixir`
最后，您可以开始构建源代码：

`% make clean test`
看到所有消息经过是相当迷人的 - 它永远不会过时。完成后，还有一个额外的步骤：您需要将`elixir`目录添加到您的`PATH`中，以便您可以访问`elixir`和`iex`等命令。

根据您的shell，您可以将`elixir`目录附加到您的`PATH`。例如，如果我要使用`zsh`，那么我会定位到`~/.zshrc`并附加目录：

`export PATH= ... # 其他PATH在这里 export PATH=$PATH:"~/elixir"`
在这里，我指定了一个`PATH`是位于我的家目录下的`elixir`目录。

## A.4 验证您的Elixir安装

最后要做的是检查Elixir是否已正确安装：

`% elixir -v`
如果一切顺利，您将看到Erlang/OTP版本和Elixir版本：

`Erlang/OTP 18 [erts-7.2] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]  Elixir 1.3.2`
您还在等什么？继续第1章吧！


[****[1]****](#ulZ3weFoR2csTrcsjKXzrfG) https://www.erlang-solutions.com/resources/download.html
[****[2]****](#uVJT5MoKQk8Ut7nrzybS9dC) https://repo.hex.pm/elixir-websetup.exe

