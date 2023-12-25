xml version='1.0' encoding='utf-8'?



Style A ReadMe






# 10           Dialyzer and Type Specifications


This chapter covers:


·      What is Dialyzer and how it works


·      Finding discrepancies in your code with Dialyzer


·      Writing type specifications and defining your own types


Depending on your inclination, the mere mention of types could either send you shrieking with joy or recoiling in terror. Being a dynamically typed language, Elixir spares you from having to pepper your code base with types à la Haskell. Some might argue that this leads to a quicker development cycle. However, the Elixir programmer shouldn’t get too smug. Statically typed languages can catch a whole class of errors at *compile* time that a dynamic language can only catch at *runtime*.


Fortunately for us, the fault-tolerance features baked into the language try to save us from ourselves. Languages without these features (Ruby, I’m looking at you) will just crash. However, it is our responsibility to make our software as reliable as possible. In this chapter, we will learn how to exploit types to do that.


We will learn about Dialyzer, a tool that comes bundled with the Erlang distribution. This power tool is used to weed out certain classes of software bugs. The best part? You don’t have to do anything special to your code.


You will learn some of the interesting theory behind how Dialyzer works. That will help you decipher its (sometimes cryptic) error messages. You will also understand why Dialyzer is not a silver bullet to solve all the your typing woes.


In last part of this chapter, we will learn how we can make Dialyzer to a better job at hunting for bugs by sprinkling our code with types. By the end of this chapter, you will learn how to integrate Dialyzer as part of your development workflow.


Whoever came up with the name Dialyzer deserves a raise for the awesome telecom-related acronym. Dialyzer stands for DIscrepancy Analyze for ERlang. Dialyzer is a tool that helps you find discrepancies in your code. Exactly what kind? Here’s a list:


·      Type Errors


·      Exception-raising code


·      Unsatisfiable conditions


·      Redundant code


·      Race conditions


We will see for ourselves how Dialyzer can pick up some these discrepancies soon. Before that, it is helpful to understand how Dialyzer works under the hood.


10.1       How does Dialyzer Work


Static languages can catch potential errors at compile time. Dynamic language, by their very nature, can only detect these errors at runtime. Dialyzer attempts to bring some of the benefits of static type-checkers to a dynamic language like Elixir/Erlang.


One of the main objectives of Dialyzer is not to get in the way of existing programs. This means that no Erlang (and Elixir) programmer should be expected to rewrite code just to accommodate Dialyzer.


This leads to a very nice outcome: You do not need to provide Dialyzer any additional information for it to do its work. That is not to say that you *can’t*. In fact, as you will see later on, you can provide additional type information that can let Dialyzer do a better job at hunting down discrepancies.


10.2       Success Typings


Dialyzer uses the notion of *success typings* to gather and infer type information. It is worth getting an idea of how Dialyzer works. To understand what success typings are, we need to understand a little bit about the Elixir type system.


A dynamic language such as Elixir requires a type system that is more relaxed than a static type system, since functions can potentially take in multiple types of arguments.


Let’s look at the Boolean “and” function for example. In a static language such as Haskell, the
`and`
function could be implemented like so:

`and :: Bool -> Bool -> Bool`
`and x y | x == True && y == True = True``| otherwise = False`
The first line
`and :: Bool -> Bool -> Bool`
is the type signature of the function. It says that
`and`
is a function that accepts two Booleans as an argument and returns a Boolean. If the type checker sees anything else other than Booleans as inputs to
`and`, your program will not make it pass compilation. How would an Elixir version look like?


Listing 10.1 Boolean and implemented in Elixir

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
Thanks to pattern matching, we can express
`and/2`
as three function clauses. What are valid arguments to
`and/2`? Both the first and second argument accepts
`true`,
`false`, and
`_`
while the return values are all Booleans.


The “\_” as you already know means “anything under the sun”. Therefore, these are perfectly ok invocations of
`and/2`:

`MyBoolean.and(false, "great success!")`
`MyBoolean.and([1, 2, 3], false)`
A Haskell type checker will not allow a program like the Elixir one presented earlier, because it doesn’t allow “anything under the sun” as a type. It cannot handle such an uncertainty.


Dialyzer on the other hand, employs a different typing inference algorithm called success typings. Success typings are very optimistic. It always assumes that all your functions are used correctly. Therefore your code is innocent until proven guilty.


Success typings start with *over-approximating* the valid inputs and outputs to your functions. So it starts with assuming that your function can take it anything and it returns anything. However, as it understands your code better, it generates *constraints*. These constraints will in turn restrict the value inputs and as a consequence, the output.


For example, if it sees
`x + y`, then
`x`
and
`y`
must definitely be numbers. Guards such as
`is_atom(z)`
also provide additional constraints. Once the constraints are generated, it is time to *solve* them, just like a puzzle. The solution to the puzzle is the success typing of the function. Conversely, if no solution is found, the constraints are *unsatisfiable* and you have a type violation on your hands.


However, it is important to realize that because Dialyzer starts with always assuming your code is right, it *doesn’t* guarantee that your code is type-safe. Now, before you get up and leave the room, there is a very nice property that arises from this. If Dialyzer finds something wrong, it is *guaranteed* to be right. So the first lesson of Dialyzer is this:



Dialyzer is never wrong!


`Dialyzer is \_always\_ right if it says your code is wrong.`

 



This is why when Dialyzer says that your code is messed up, it is 100% correct. Stricter type-checkers begin with assuming that your code is wrong, and that your code must type-check successfully before it is allowed to compile. This also means that your code is guaranteed (more or less) to be type-safe.


So to reiterate: Dialyzer will *not* (or ever) discover all type-violations. However, if it finds a problem, then your code is *guaranteed* to be problematic. Now that we have some background on how success typings work, let’s turn our attention to finding out about types in Elixir.


10.3       Revealing Types in Elixir, Part I


We’ve been using Elixir without much emphasis on the exact types. In this section and the next, we will pay slightly more attention.


From Elixir 1.2 onwards, there is a very handy helper in
`iex`
that prints information about the given data type called
`i/1`. For example, what is the difference between
`"ohai"`
and
`'ohai'`
(note the use of double and single quotes respectively)? Let’s find out:


Listing 10.2 Using i/1 to reveal the type of an Elixir string

`iex> i("ohai")`
`Term`
`"ohai"`
`Data type`
`BitString`
`Byte size`
`4`
`Description`
`This is a string: a UTF-8 encoded binary. It's printed surrounded by`
`"double quotes" because all UTF-8 codepoints in it are printable.`
`Raw representation`
`<<111, 104, 97, 105>>`
`Reference modules``String, :binary`
And let’s now contrast it with
`'ohai'`:


Listing 10.3 Using i/1 to reveal the type of a character list

`iex> i('ohai')`
`Term`
`'ohai'`
`Data type`
`List`
`Description`
`This is a list of integers that is printed as a sequence of codepoints`
`delimited by single quotes because all the integers in it represent valid`
`ascii characters. Conventionally, such lists of integers are referred to as`
`"char lists".`
`Raw representation`
`[111, 104, 97, 105]`
`Reference modules``List`
Next time if you are getting type errors and are confused, reach immediately for the
`i/1`
helper.


10.4       Getting Started with Dialyzer


Dialyzer can either use Erlang source code or debug-compiled BEAM byte-code. Obviously, this leaves us with the latter option. This means that before we run Dialyzer we must remember to do a
`mix compile`.



Remember to compile first!



Since starting to use Dialyzer I have lost count about the number of times I have forgotten this step. Fortunately, once I have discovered Dialyxir (you will see this later on), I no longer have to manually compile my code.



 



Dialyzer comes installed with the Erlang distribution and exists as a command-line program:

`% dialyzer`
`Checking whether the PLT /Users/benjamintan/.dialyzer_plt is up-to-date...`
`dialyzer: Could not find the PLT: /Users/benjamintan/.dialyzer_plt`
`Use the options:`
`--build_plt   to build a new PLT; or`
`--add_to_plt  to add to an existing PLT`

`For example, use a command like the following:`
`dialyzer --build_plt --apps erts kernel stdlib mnesia`
`Note that building a PLT such as the above may take 20 mins or so`

`If you later need information about other applications, say crypto,`
`you can extend the PLT by the command:`
`dialyzer --add_to_plt --apps crypto``For applications that are not in Erlang/OTP use an absolute file name.`
Awesome, we have convinced ourselves that Dialyzer is indeed installed. But what is this *PLT* that Dialyzer is trying to search for?


10.4.1     The PLT: The Persistent Lookup Table


The PLT stands for Persistent Lookup Table. Dialyzer uses the PLT to store the result of its analysis. You can also use a previously constructed PLT that serves as a starting point for Dialyzer. This becomes important because any non-trivial Elixir application would probably involve OTP. If we run Dialyzer on such an application, the analysis will undoubtedly take a long time.


Since the OTP libraries will not change, we can always build a “base PLT” and only run Dialyzer on our application, which by comparison will take a much shorter time. The flip side of this is that once you upgrade Erlang and/or Elixir, you must be remember to rebuild the PLT.


10.4.2     Dialyxir


Traditionally, running Dialyzer involves quite a bit of typing. Thankfully, thanks to the laziness of programmers there are libraries that contain
`mix`
tasks that make our lives easier. The one that we are going to use is *Dialyxir*. Dialyxir contains
`mix`
tasks that make Dialyzer a joy to use in Elixir projects.


Dialyxir can either be installed as a dependency (as we will see later) or it can be installed globally. We will install Dialyxir globally first, so that we can build the PLT table. This is not strictly necessary, but is useful when you don’t want to install Dialyxir as a project dependency:

`git clone https://github.com/jeremyjh/dialyxir`
`cd dialyxir`
`mix archive.build``mix archive.install`
Let’s start using Dialyxir!


10.4.3     Building a PLT Table


As previously mentioned, we need to build a PLT first. Happily, Dialyxir has a mix task to build a PLT:

`% mix dialyzer.plt`
Grab a coffee because this will take a while:

`Starting PLT Core Build ... this will take awhile`
`dialyzer --output_plt /Users/benjamintan/.dialyxir_core_18_1.2.0-rc.1.plt --build_plt --apps erts kernel stdlib crypto public_key -r /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../eex/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../elixir/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../ex_unit/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../iex/ebin /usr/local/Cellar/elixir/HEAD/bin/../lib/elixir/../mix/ebin`
`...`
`cover:compile_beam_directory/1`
`cover:modules/0`
`cover:start/0`
`fprof:analyse/1`
`fprof:apply/3`
`fprof:profile/1`
`httpc:request/5`
`httpc:set_options/2`
`inets:start/2`
`inets:stop/2`
`leex:file/2`
`yecc:file/2`
`Unknown types:`
`compile:option/0`
`done in 2m33.16s``done (passed successfully)`
You don’t have to worry about “Unknown types” and other warnings as long as the PLT was built successfully.


10.5       Software Discrepancies that Dialyzer can Detect


In this section, we will create a project to play with. The example project is a simple currency converter that only converts Singapore Dollars to United States dollars. Create the project:

`% mix new dialyzer_playground`
Open up
`mix.exs`
and add Dialyxir:


Listing 10.4 Add the dialyxir dependency (mix.exs)

`defmodule DialyzerPlayground.Mixfile do`
`# ...`

`defp deps do`
`[{:dialyxir, "~> 0.3", only: [:dev]}]`
`end``end`
As usual, remember to run
`mix deps.get`. Now the fun begins!


10.5.1     Catching Type Errors


We begin with a simple example that demonstrates how Dialyzer can catch simple type errors. Create
`lib/bug_1.ex`:


Listing 10.5 Cashy.Bug1 has a type error. Can you spot it? (lib/bug\_1.ex)

`defmodule Cashy.Bug1 do`

`def convert(:sgd, :usd, amount) do`
`{:ok, amount * 0.70}`
`end`

`def run do`
`convert(:sgd, :usd, :one_million_dollars)`
`end`
`end`
The
`convert/3`
function takes in three arguments. The first two arguments *must* be the atoms
`:sgd`
and
`:usd`
respectively.
`amount`
is assumed to be a number and is used to compute the exchange rate from Singapore dollars to United States dollars. Pretty straightforward stuff.


Now imagine that
`run/1`
function that could live on another module. It is not inconceivable to have someone use this function wrongly, such as passing in at atom as the last argument to
`convert/3`, instead of a number.


The problem with the code only suffice the moment
`run/1`
is executed. Otherwise, this problem might not even surface. It is worthwhile to note that a statically typed language will never allow for code like this. Good thing for us, we have Dialyzer! Let’s run Dialyzer and see what happens:

`% mix dialyzer`
Here’s the output:

`% mix dialyzer`
`Compiled lib/bug_1.ex`
`Generated dialyzer_playground app`
`...`
`Proceeding with analysis...`
`bug_1.ex:7: Function run/0 has no local return`
`bug_1.ex:8: The call 'Elixir.Cashy.Bug1':convert('sgd','usd','one_million_dollars') will never return since it differs in the 3rd argument from the success typing arguments: ('sgd','usd',number())`
`done in 0m1.00s``done (warnings were emitted)`
Dialyzer has found us a problem! “no local return” in Dialyzer-speak means that the function will definitely fail. This usually means that Dialyzer has found a type error and has therefore determined that the function can never return.


As it rightly pointed out,
`convert/3`
will never return because the arguments that we have given it will cause an
`ArithmeticError`.


10.5.2     Wrong Use of Built-In Functions


Let’s examine another case. Create
`lib/bug_2.ex`:


Listing 10.6 Cashy.Bug2 has a wrong use of a built-in function. (lib/bug\_2.ex)

`defmodule Cashy.Bug2 do`

`def convert(:sgd, :usd, amount) do`
`{:ok, amount * 0.70}`
`end`

`def convert(_, _, _) do`
`{:error, :invalid_amount}`
`end`

`def run(amount) do`
`case convert(:sgd, :usd, amount) do`
`{:ok, amount} ->`
`IO.puts "converted amount is #{amount}"`

`{:error, reason} ->`
`IO.puts "whoops, #{String.to_atom(reason)}"`
`end`
`end`
`end`
The first function clause is identical to the one in
`Cashy.Bug1`. In addition, there is a catch-all clause that returns
`{:error, :invalid_amount}`. Once again, imagine
`run/1`
is called by some client code elsewhere. Can you spot the problem? Let’s see what Dialyzer says:

`% mix dialyzer`
`...`
`bug_2.ex:18: The call erlang:binary_to_atom(reason@1::'invalid_amount','utf8') breaks the contract (Binary,Encoding) -> atom() when is_subtype(Binary,binary()), is_subtype(Encoding,'latin1' | 'unicode' | 'utf8')`
`done in 0m1.02s``done (warnings were emitted)`
Interesting! There seems to be a problem with:

`erlang:binary_to_atom(reason@1::'invalid_amount','utf8')`
It seems to be breaking some form of contract. On line 18, as Dialyzer points out, we are invoking
`String.to_atom/1`. Seems like this is causing the problem. The contract that
`erlang:binary_to_atom/2`
is looking for is

`(Binary,Encoding) -> atom()`
What we are supplying as inputs are
`'invalid_amount' and 'utf8'`
which work out to be
`(Atom, Encoding)`. On closer inspection, we should have called
`Atom.to_string/1`
instead of
`String.to_atom/1`. Whoops.


10.5.3     Redundant Code


Dead code impedes maintainability. In certain cases, Dialyzer can analyze code paths and discover redundant code.
`lib/bug_3.ex`
provides an example of this:


Listing 10.7 Cashy.Bug3 has a redundant code path. (lib/bug\_3.ex)

`defmodule Cashy.Bug3 do`

`def convert(:sgd, :usd, amount) when amount > 0 do`
`{:ok, amount * 0.70}`
`end`

`def run(amount) do`
`case convert(:sgd, :usd, amount) do`
`amount when amount <= 0 ->`
`IO.puts "whoops, should be more than zero"`
`_ ->`
`IO.puts "converted amount is #{amount}"`
`end`
`end`
`end`
This time, we have added a guard clause to
`convert/2`, making sure that the currency conversion takes place only when
`amount`
is larger than zero. Take a look now at
`run/1`. It has two clauses. One of them handles the case when
`amount`
is lesser or equal to zero. The second clause handles when
`amount`
is larger. What does Dialyzer say about this?

`% mix dialyzer`
`...`
`bug_3.ex:9: Guard test amount@2::{'ok',float()} =< 0 can never succeed`
`done in 0m0.97s``done (warnings were emitted)`
Dialyzer has helpfully identified some redundant code! Since we have the guard clause in
`convert/3`, we can be sure that the
`amount <= 0`
case will never happen. Again, this is a trivial example. However, it is not hard to imagine that a programmer could easily not know this behavior and therefore try to cover all the cases, when in fact this is redundant.


10.5.4     Type Errors in Guard Clauses


Type errors can occur in the case where guard clauses are used. Guard clauses constrain the types of the arguments that they wrap. In this next example, that argument is
`amount`. Let’s take a look at
`lib/bug_4.ex`. You might be able to spot the problem easily:


Listing 10.8 There will be an error when run/1 executes. Can you guess why? (lib/bug\_4.ex)

`defmodule Cashy.Bug4 do`

`def convert(:sgd, :usd, amount) when is_float(amount) do`
`{:ok, amount * 0.70}`
`end`

`def run do`
`convert(:sgd, :usd, 10)`
`end`
`end`
Let Dialyzer do its thing:

`% mix dialyzer`
`...`
`bug_4.ex:7: Function run/0 has no local return`
`bug_4.ex:8: The call 'Elixir.Cashy.Bug4':convert('sgd','usd',10) will never return since it differs in the 3rd argument from the success typing arguments: ('sgd','usd',float())`
`done in 0m0.97s``done (warnings were emitted)`
If we stare hard enough we would have realized that
`10`
is not of type
`float()`
and therefore fails the guard clause. An interesting thing about guard clauses is that they will never throw exceptions, which is the whole point since you are specifically allowing only certain kinds of input. However, this might sometimes lead to confusing bugs such as the one above when is seems like
`10`
should be allowed past the guard clause.


10.5.5     Tripping Up Dialyzer with Some Indirection


In the last example of this section, we look at a slightly modified version of
`Cashy.Bug1`. Create
`lib/bug_5.ex`:


Listing 10.9 Dialyzer will not be able to catch this bug. (lib/bug\_5.ex)

`defmodule Cashy.Bug5 do`

`def convert(:sgd, :usd, amount) do`
`amount * 0.70`
`end`

`def amount({:value, value}) do`
`value`
`end`

`def run do`
`convert(:sgd, :usd, amount({:value, :one_million_dollars}))`
`end`
`end`
Now, it would seem obvious that Dialyzer would most likely report the same bugs as it did for
`Cashy.Bug1`. Notice here that we have merely added a layer of indirection by making the
`amount/1`
a function call that returns the actual value of the amount we want to convert. Let’s test our hypothesis:

`% mix dialyzer`
`...`
`Proceeding with analysis... done in 0m1.05s``done (passed successfully)`
Oh wait, what? Unfortunately in this instance, Dialyzer cannot detect the discrepancy because of this indirection. This is a perfect segue into the next topic on type specifications. We will come back to
`Cashy.Bug5`
after that.


10.6       Type Specifications


We have mentioned that Dialyzer can happily run without any help from you. We have shown you some examples of the software discrepancies that Dialyzer can detect from
`Cashy.Bug1`
through
`Cashy.Bug4`.


However as
`Cashy.Bug5`
has shown, all is not rainbows and unicorns. While Dialyzer could report
`passed successfully`, that doesn’t mean that your code is free of bugs. There are some cases where Dialyzer cannot detect completely on its own.


With some effort, we can help Dialyzer to potentially reveal hard-to-detect bugs. We do this by adding *type specifications*, or *Typespecs* for short.


The other advantage of adding type specifications to your code is that it serves as a form of documentation. Especially with dynamic languages, it is sometimes not obvious what are valid inputs and what the type of the return value. In this section, you will learn how to write your own type specifications not only to write better documentation, but also to write more reliable code.


10.6.1     Writing Type Specifications


The best way to show you how to work with type specifications is through a few examples. The format of defining a type specification is:

`@spec function_name(type1, type2) :: return_type`
The format should be self-explanatory. We will cover what are valid values of types later on (`type1`,
`type2`
and
`return_type`). Here are some of the types and type unions that have already been pre-defined (these will make more sense when you work through the examples). These are not exhaustive, but rather a good sampling of the available types.




|  |  |
| --- | --- |
| 
Type
 | 
Description
 |
|
`term`
| This is defined as
`any`.
`term`
represents any valid Elixir term, and this also includes functions with
`_`
as the argument. |
|
`boolean`
| This is defined as the union of both Boolean types –
`false | true`.
`char`: This is defined as the range of valid characters:
`0..0x10ffff`. Note that
`..`
is the range operator. |
|
`number`
| This is defined as the union of integers and floats –
`integer | float`. |
|
`binary`
| Use this for Elixir strings. |
|
`char_list`
| Use this for Erlang strings. This is defined as
`[char]`. |
|
`list`
| This is defined as
`[any]`. You can always constrain the type if the list. For example,
`[number]`. |
|
`fun`
|
`(... -> any)`
represents *any* anonymous function. You might want to constrain this based the functions arity and return type. For example,
`(() -> integer)`
is an arity-zero anonymous function that returns an integer, while
`(integer, atom -> [boolean])`
is an arity-two function that takes an integer and an atom respectively, and returns a list of Booleans. |
|
`pid`
| A process id |
|
`tuple`
| Any kind of tuple. Other valid options are
`{}`
and
`{:ok, binary}`. |
|
`map`
| Any kind of map. Other valid options are
`%{}`
and
`%{atom => binary}`
|


Table 10. 1 Some of the available types for use in type-specifications


The next few examples will give you a better feel.


Example: Addition


Let’s start with a simple add function that takes two numbers and returns another number. This is one possible type specification:


Listing 10.10 A possible type specification for add/2

`@spec add(integer, integer) :: integer`
`def add(x, y) do`
`x + y``end`
As it stands,
`add/2`
might be too restrictive. We might also want to include floats *or* integers. The way to write that would be:


Listing 10.11 Including both floats and numbers as input arguments and return values

`@spec add(integer | float, integer | float) :: integer | float`
`def add(x, y) do`
`x + y``end`
Thankfully, we can use the built-in shorthand type
`number`, which is defined as
`integer | float`. The
`|`
means that
`number`
is a union type. As the name suggests, a union type is a type that is made up of two or more types. The union type can apply to both input types and the types of return values.


Listing 10.12 Using the number shorthand to represent integer | float

`@spec add(number, number) :: number`
`def add(x, y) do`
`x + y``end`
We will see more examples of union types soon when we learn how to define our own types.


Example: List.fold/3


Let’s try to tackle something more challenging:
`List.fold/3`. This function reduces the given list from the left with a function. It also requires a starting value for the accumulator. Here is how the function works:

`iex> List.foldl([1, 2, 3], 10, fn (x, acc) -> x + acc end)`
As expected, the function will return
`16`. The first argument is the list, followed by the starting value of the accumulator. The last argument is the function that performs each step of the reduction. Here is the function signature (taken from the
`List`
source code):


Listing 10.13 The function signature of List.foldl

`def foldl(list, acc, function)`
`when is_list(list) and is_function(function) do`
`# the implementation is not important here``end`
`List.foldl/3`
already constrains the type of
`list`
to be well, a list, due to the
`is_list/1`
guard clause. However, the elements of the list can be any valid Elixir term. The same goes for
`function`
needing to be an actual function.
`function`
has to be an arity of two, where the first argument is the same type as
`elem`
and the second argument the same type as
`acc`. Finally, the return result of this function should be the same type as
`acc`. One possible way to specify the type specification of
`List.foldl/3`
could be:


Listing 10.14 One possible (but not very helpful) way to writing the type specification of List.foldl/3

`@spec foldl([any], any, (any, any -> any)) :: any`
`def foldl(list, acc, function)`
`when is_list(list) and is_function(function) do`
`# the implementation is not important here``end`
While there is technically nothing wrong with this type specification as far as Dialyzer is concerned, it doesn’t show the relation between the types between the input arguments and the return value. We can use type variables with no restriction given as arguments to the function like so:

`@spec function(arg) :: arg when arg: var`
Note the
`var`, which means any variable. Therefore, we can supply better variable names to the type specification like so:


Listing 10.15 Providing better variable names in the type specification

`@spec foldl([elem], acc, (elem, acc -> acc)) :: acc when`
`elem: var, acc: var`
`def foldl(list, acc, function)`
`when is_list(list) and is_function(function) do`
`# the implementation is not important here``end`
Example: Map Function


We can also use guards can be used to restrict type variables given as arguments to the function like so:

`@spec function(arg) :: arg when arg: atom`
In this example, we have our own implementation of
`Enum.map/2`. Create
`lib/my_enum.ex`. Notice the type specifications of the individual arguments and return result.


Listing 10.16 A type specification for the map function (lib/my\_enum.ex0

`defmodule MyEnum do`

`@spec map(f, list_1) :: list_2 when`
`f: ((a) -> b),`
`list_1: [a],`
`list_2: [b],`
`a: term,`
`b: term`
`def map(f, [h|t]), do: [f.(h)| map(f, t)]`

`def map(f, []) when is_function(f, 1), do: []`
`end`
From the type specification, we are declaring that:


·     
`f`
(the first argument to
`map/2`
is a single-arity function that takes in a term and return another term


·     
`list_1`
(the second argument to
`map/2`) and
`list_2`
(the return result of
`map/2`
are a list of terms.


We have also taken pains to name the input and output types of
`f`. While this is not strictly necessary, having explicitly put
`a`
and
`b`
says that
`f`
operates on a type
`a`
and returns a type
`b`, and that
`map/2`
takes as input a list of type
`a`
and outputs a list of type
`b`. As you can see, type specifications can convey a lot of information.


10.7       Writing your own Types


You can define your own types using
`@type`. For example, let’s come up with a custom type for RGB color codes. Create
`lib/hexy.ex`:


Listing 10.17 Using @type to define custom types (lib/hexy.ex)

`defmodule Hexy do`
`@type rgb() :: {0..255, 0..255, 0..255}           #1`
`@type hex() :: binary                             #2`

`@spec rgb_to_hex(rgb) :: hex                      #3`
`def rgb_to_hex({r, g, b}) do`
`[r, g, b]`
`|> Enum.map(fn x -> Integer.to_string(x, 16) |> String.rjust(2, ?0) end)`
`|> Enum.join`
`end``end`
#1 Type alias for a RGB color code


#2 Type alias for a Hex color code


#3 Using the custom type definitions in the specification


We could have just specify
`@spec rgb_to_hex(tuple) :: binary`, but that doesn’t convey a lot of information, neither does it constrain the input arguments much except to say that a tuple is expected. In this case, even an empty one is acceptable.


Instead, specified a tuple with three elements, and further specified that each element are integers which range from 0 to 255. Finally, we gave the type a descriptive name like
`rgb`. For
`hex`, instead of calling it simply
`binary`
(a string in Elixir), we aliased it to
`hex`
just to be more descriptive.


10.7.1     Multiple Return Types and Bodiless Function Clauses


It is not uncommon to have functions that consist of multiple return types. In this case, we can use *bodiless function clause*s to group type annotations together. Consider the following:


Listing 10.18 Using a bodiless function clause and attaching the type specification to that (lib/hexy.ex)

`defmodule Hexy do`
`@type rgb() :: {0..255, 0..255, 0..255}`
`@type hex() :: binary`

`@spec rgb_to_hex(rgb) :: hex | {:error, :invalid}`
`def rgb_to_hex(rgb) #1`

`def rgb_to_hex({r, g, b}) do`
`[r, g, b]`
`|> Enum.map(fn x -> Integer.to_string(x, 16) |> String.rjust(2, ?0) end)`
`|> Enum.join`
`end`

`def rgb_to_hex(_) do`
`{:error, :invalid}`
`end``end`
#1 The bodiless function clause


This time,
`rgb_to_hex/1`
has two clauses. The second clause is the fallback case. This fallback case will always return
`{:error, :invalid}`. This means that we have to update our type specification.


Instead of writing it above the first function clause like we did in the previous example, we can create a *bodiless* function clause. One thing to note is how we defined the clause. This will work:

`def rgb_to_hex(rgb)`
While this will *not* work:

`def rgb_to_hex({r, g, b})`
If you tried to compile the file, you would get an error message:

`** (CompileError) lib/hexy.ex:7: can use only variables and \\ as arguments of bodiless clause`
Having a bodiless function clause is useful to group all the possible type specifications in one place, which saves you from sprinkling the type specifications on every function clause.


10.7.2     Revealing Types in Elixir, Part II


Besides
`i/1`, there is another handy
`iex`
helper:
`t/1`.
`t/1`
prints the types for the given module or for the given function/arity pair. This is handy if you wanted to know more about the types (possibly custom) used in a module. For example, let’s investigate the types found in
`Enum`:

`iex> t Enum`
`@type t() :: Enumerable.t()`
`@type element() :: any()`
`@type index() :: non_neg_integer()``@type default() :: any()`
Here, we can see that
`Enum`
has four defined types.
`Enumerable.t`
looks interesting. The
`Enumerable`
module also has a bunch of defined types:

`iex> t Enumerable`
`@type acc() :: {:cont, term()} | {:halt, term()} | {:suspend, term()}`
`@type reducer() :: (term(), term() -> acc())`
`@type result() :: {:done, term()} | {:halted, term()} | {:suspended, term(), continuation()}`
`@type continuation() :: (acc() -> result())``@type t() :: term()`
10.7.3     Back to Bug #5


Before we end of this chapter, let’s come back to
`Cashy.Bug5`
as promised. Without any type specifications, Dialyzer was unable to find the obvious bug. However, let’s add in the type specifications now:


Listing 10. 19 Adding type specifications to Cashy.Bug5 (lib/bug\_5.ex)

`defmodule Cashy.Bug5 do`

`@type currency() :: :sgd | :usd`

`@spec convert(currency, currency, number) :: number`
`def convert(:sgd, :usd, amount) do`
`amount * 0.70`
`end`

`@spec amount({:value, number}) :: number`
`def amount({:value, value}) do`
`value`
`end`

`def run do`
`convert(:sgd, :usd, amount({:value, :one_million_dollars}))`
`end`
`end`
This time when we run Dialyzer, it shows an error that we *didn’t* expect, and one we expected but didn’t get previously:

`bug_5.ex:22: The specification for 'Elixir.Cashy.Bug5':convert/3 states that the function might also return integer() but the inferred return is float()`

`bug_5.ex:32: Function run/0 has no local return`
`bug_5.ex:33: The call 'Elixir.Cashy.Bug5':amount({'value','one_million_dollars'}) breaks the contract ({'value',number()}) -> number()`
`done in 0m1.05s``done (warnings were emitted)`
Let’s deal with the second, more straightforward error first. Since we are passing in an atom (`:one_million_dollars`) instead of a number, Dialyzer rightly complains.


What about the second error? It is saying that our type specifications say that an
`integer`
could be returned, but what Dialyzer has inferred is that the function only returns
`float`. Now when we inspect the body of the function, we see:

`amount * 0.70`
Of course! Multiplying with a float will always return a float! That is why Dialyzer was complaining. This is nice because Dialyzer is able to check our type specifications in some cases for obvious errors.


10.8       Exercises


1.  Play around with
`Cashy.Bug1`
through
`Cashy.Bug5`
and try to add erroneous type specifications. See if the error messages make sense to you. A harder exercise is to devise code that has an obvious error but Dialyzer fails to catch the bug. This is something that we have done in
`Cashy.Bug5`.


2.  Imagine you are writing a card game. A card consists of a suit and a value. Come up with types for a card, a suit and the cards value. To get you started:

`@type card :: {suit(), value()} @type suit :: <FILL THIS IN> @type value :: <FILL THIS IN>`
3.  Try your hand at specifying the types for some built-in functions. A good place to start is the
`List`
and
`Enum`
module. A good source of inspiration is the Erlang/OTP (yes, Erlang!) code base. The syntax is slightly different, but should pose no major obstacle for you.


10.9       Summary


Dialyzer has been used in production to great effect. It has discovered software discrepancies in OTP, for example, that hasn’t been discovered before. While it is no silver bullet, Dialyzer provides some of the benefits of a static type checker that languages such as Haskell have.


Including types in your functions not only serve as documentation, it also allows Dialyzer to be more accurate in spotting discrepancies. As an added benefit, Dialyzer can also point out if you have made a mistake in the type specification. In this chapter, we learnt about:


·      Success typings, the type inference mechanism that Dialyzer uses


·      How to use Dialyzer and interpret its sometimes cryptic error messages


·      How to increase the accuracy of Dialyzer by providing type specifications and guards like
`is_function(f, 1)`
and
`is_list(l)`


In the next chapter, we look at testing tools that have been written specially for the Erlang eco-system. These tools are not the run of the mill unit-testing tools. These power tools can generate test cases based on general properties that you define and hunt down concurrency errors.





