# 2   A Whirlwind Tour


This chapter covers:


·      Your first Elixir program


·      Using Interactive Elixir (iex)


·      Data Types


·      Pattern Matching


·      List and Recursion


·      Modules and Functions


·      The Pipe (|>) operator


·      Erlang Interoperability


Instead of going in-depth into each language feature, I thought it would be better to present them as a series of examples.  I will elaborate more when we come to concepts that might seem unfamiliar to, say, a Java or Ruby programmer. For certain concepts, you can probably draw parallels from whatever languages you already know. Each of these examples will get progressively more fun, and highlight almost everything you need to understand the Elixir code in this book.


2.1           Setting Up Your Environment


Elixir is pretty much supported on all the major editors such as Vim, Emacs, Spacemacs, Atom, IntelliJ and Visual Studio, just to name a few. The aptly named Alchemist[[1]](#uRD9OOhUuHjWvTh2WNVJTqC), the Elixir tooling integration that works with Emacs/Spacemacs provides for an excellent developer experience. It features things like documentation lookup, smart code completion, integration with
`iex`
and
`mix`
and a ton of other useful features. It is by far the most supported and feature-rich compared with the rest of the editor integration.


Get your terminal and editor ready, because the whirlwind tour begins now.


2.2           First Steps


Let's begin with something simple. Due to my former colonial masters (I'm from Singapore), I am woefully unfamiliar with measurements in feet, inches and its cousins. We are going to write a length converter to remedy that.


Here is how we could define the length converter in Elixir. Enter the following into your favorite text editor and save the file as
`length_converter.ex`.


Listing 2.1 The length converter program in Elixir. Save this as length\_converter.ex.

`defmodule MeterToFootConverter do`
`def convert(m) do`
`m * 3.28084`
`end``end`
`defmodule`
defines a new module (i.e.
`MeterToFootConverter`) and
`def`
defines a new function (i.e.
`convert`).


2.2.1        Here Running an Elixir program in Interactive Elixir


`iex`, or Interactive Elixir for short, is the equivalent of
`irb`
in Ruby or
`node`
in NodeJS. In your terminal, launch
`iex`
with the file name as the argument.


Listing 2.2 Running the length converter program (Interactive Elixir)

`% iex length_converter.ex`

`Interactive Elixir (0.13.0) - press Ctrl+C to exit (type h() ENTER for help)``iex(1)>`
The record for the tallest man in the world is 2.72 m. What is that in feet? Let's find out:

`iex> MeterToFeetConverter.convert(2.72)`
gives

`8.9238848`
2.2.2        Stopping an Elixir program


There are a few ways to stop an Elixir program, or if you want to exit iex. The first way is typing
`Ctrl + C`. The first time you do this, you will see:


Listing 2.3 Stopping a running Elixir program in iex (Interactive Elixir)

`BREAK: (a)bort (c)ontinue (p)roc info (i)nfo (l)oaded`
`(v)ersion (k)ill (D)b-tables (d)istribution`
You could either a) type
`a`
to abort, or b) type
`Ctrl + C`
again. An alternative would be to use
`System.halt`, although personally I’m more of a
`Ctrl + C`
person.


2.2.3        Getting Help


Since
`iex`
is your primary tool for interacting with Elixir, it pays to learn a bit more about it. In particular,
`iex`
features a pretty sweet built-in documentation system. Fire up
`iex`
again. Let's say you wanted to learn about the
`Dict`
module. You would type
`h Dict`
in
`iex`
and the output will be similar to figure 2.3.


![](../images//2_3.png)  



Figure 2.3 Documentation of the Dict module displayed in iex.


What are the available functions of
`Dict`? Type
`Dict.`
(the dot is important!) followed by your
`<Tab>`
key. You will see a list of functions available in the
`Dict`
module as shown in figure 2.4.


![](../images//2_4.png)  



Figure 2**.**4 A list of functions available in the
`Dict`
module.


Now, let’s say you want to learn more about the
`put/3`
function. I will explain what the
`/3`
means later. For now, it just means that this version of
`put`
accepts 3 arguments. In
`iex`, type
`h Dict.put/3.`
The output will look like figure 2.5:


![](../images//2_5.png)  



Figure 2.5 Documentation of
`Dict.put/3`.


Pretty neat, eh? What's even better is that the documentation is beautifully syntax-highlighted.


2.3           Data Types


Here are the common data types we will use in this book:


·      Modules


·      Functions


·      Numbers


·      Strings


·      Atoms


·      Tuples


·      Maps


2.3.1        Modules, Functions and Function Clauses


Modules are Elixir's way of grouping functions together. Examples of modules are
`List`,
`String`, and of course,
`MeterToFootConverter`. A module is created using
`defmodule`. Similarly, functions are created using
`def`.


Modules


Just for kicks, let's write another function to convert meters into *inches*. Given our current implementation, we need to make a few changes. Firstly, our module name is *too specific*. Let's change that to something more general. Here is our
`length_converter.ex`
again:

`defmodule MeterToLengthConverter do`
`# ...``end`
More interestingly, how would we add a function that converts from meters to inches? Here is one *possible* approach:


Listing 2.4  defmodules can be nested

`defmodule MeterToLengthConverter do`
`defmodule Feet do`
`def convert(m) do`
`m * 3.28084`
`end`
`end`

`defmodule Inch do`
`def convert(m) do`
`m * 39.3701`
`end`
`end``end`
Now, you can compute the height of the tallest man in inches:


Listing 2.5  Using the dot notation (Interactive Elixir)

`iex> MeterToLengthConverter.Inch.convert(2.72)`
Returns

`107.08667200000001`
This example illustrates that modules can be nested. Here, the modules
`Feet`
and
`Inch`
are nested within
`MeterToLengthConverter`. To access a function in a nested module, the *dot notation* is used. In general, to invoke functions in Elixir, the following format is used:

`Module.function(arg1, arg2, ...)`
On mailing lists, this is sometimes known as "**MFA**". It stands for **M**odule, **F**unction and **A**rguments. Remember this format, because you will encounter them again in the book.


You can also flatten the module hierarchy like so:


Listing 2.6 Flattening the module hierarchy (Interactive Elixir)

`defmodule MeterToLengthConverter.Feet do #1`
`def convert(m) do`
`m * 3.28084`
`end`
`end`

`defmodule MeterToLengthConverter.Inch do #1`
`def convert(m) do`
`m * 39.3701`
`end``end`
#1 You can use the dot notation to specify a nested hierarchy


You would call the function exactly the same way as Listing 2.5.


Functions and Function clauses


There is a more idiomatic way of writing our length converter, and that is using function clauses. Here is a revised version of our length converter:

`defmodule MeterToLengthConverter do`
`def convert(:feet, m) do`
`m * 3.28084`
`end`

`def convert(:inch, m) do`
`m * 39.3701`
`end``end`
Defining a function is pretty straightforward. Most functions are written like this:

`def convert(:feet, m) do`
`m * 3.28084``end`
Single-lined functions are written like so:

`def convert(:feet, m), do: m * 3.28084`
While we are at it, let’s add another function to convert meters to *yards*, this time, using the single-lined variety:

`defmodule MeterToLengthConverter do`
`def convert(:feet, m), do: m * 3.28084`
`def convert(:inch, m), do: m * 39.3701`
`def convert(:yard, m), do: m * 1.09361``end`
Functions are referred to by their *arity* – the number of arguments it takes in. Therefore, we refer to the above function as
`convert/2`.
`convert/2`
is an example of a *named function*. Elixir also has the notion of *anonymous functions*. Here is a common example of an anonymous function:


Listing 2.7: Second argument is an anonymous function (Interactive Elixir)

`iex> Enum.map [1, 2, 3], fn x -> x*x end`
gives
`[1, 4, 9].`


We can define a function with the same name multiple times, just as in our example. The important thing to notice is they *must* be grouped together. Therefore, this is bad form:


Listing 2.8: Always group similar function clauses together.

`defmodule MeterToLengthConverter do`
`def convert(:feet, m), do: m * 3.28084`
`def convert(:inch, m), do: m * 39.3701`
`def i_should_not_be_here, do: IO.puts "Oops" #1`
`def convert(:yard, m), do: m * 1.09361``end`
#1 Do not do this!


And Elixir would complain accordingly:


Listing 2.10:  Elixir complains when function clauses are not grouped together.

`% iex length_converter.ex`
`length_converter.ex:5: warning: clauses for the same def should be grouped together,``def convert/2 was previously defined`
Another important thing: Order matters. Each function clause is matched in a top down fashion. This means that once Elixir finds a compatible function clause that matches, it will stop searching and execute that function. For our current length converter, moving function clauses around will not affect anything. When we explore recursion later, you will begin to appreciate why ordering of function clauses matter.


2.3.2        Numbers


Numbers in Elixir work much like how you would expect from traditional programming languages.


Listing 2.13:  Operating on  an integer, a hexadecimal, and a float (Interactive Elixir)

`iex> 1 + 0x2F / 3.0`
`16.666666666666664`
Listing 2.14:  Division and remainder functions (Interactive Elixir)

`iex> div(10,3)`
`3`

`iex> rem(10,3)``1`
2.3.3        Strings


Strings in Elixir lead two lives. On the surface, strings look like the pretty standard. Here is an example that demonstrates string interpolation:


Listing 2.15:  Elixir has string interpolation support (Interactive Elixir)

`iex(1)> "Strings are #{:great}!"`
Will give you:

`"Strings are great!"`
We can also perform various operations on strings:


Listing 2.16:  Operating on strings (Interactive Elixir)

`iex(2)> "Strings are #{:great}!" |> String.upcase |> String.reverse`
This returns:

`"!TAERG ERA SGNIRTS"`
Strings are Binaries


How do you test for a string? There isn’t an
`is_string/1`
function available. That’s because a string in Elixir is a **binary**. A binary is just a sequence of bytes.


Listing 2.17: Strings are Binaries (Interactive Elixir)

`iex(3)> "Strings are binaries" |> is_binary`
returns
`true.`


One way to show the binary representation of a string is to use the binary concatenation operator
`<>`
to attach a null byte,
`<<0>>`:


Listing 2.18: Displaying the binary representation of a String (Interactive Elixir)

`iex(4)> "ohai" <> <<0>>`
returns
`<<111, 104, 97, 105, 0>>.`


Each individual number presents a character:

`iex(5)> ?o`
`111`

`iex(6)> ?h`
`104`

`iex(7)> ?a`
`97`

`iex(8)> ?i``105`
To further convince yourself that the binary representation is equivalent:

`iex(44)> IO.puts <<111, 104, 97, 105>>`
Gives you back the original string:
`ohai`


Strings are NOT Char lists


Char lists, as its name suggests, is a list of characters. It is an entirely different data type from strings, and this can be quite confusing. While strings are always enclosed in double quotes, char lists are enclosed in single quotes.


Listing 2.19:  Strings are not char lists (Interactive Elixir)

`iex(9)> 'ohai' == "ohai"`
Will give you false. You usually will not use char lists, at least in Elixir. However, when talking to some Erlang libraries, you would have to. For example, in a later example, the Erlang http client (httpc) accepts a char list as the URL:

`:httpc.request 'http://www.elixir-lang.org'`
What happens if we passed in a string (binary) instead? Try it out:


Listing 2.20: httpc.request/1 expects a char list as the URL type (Interactive Elixir)

`iex(51)> :httpc.request "http://www.elixir-lang.org"`
`** (ArgumentError) argument error`
`:erlang.tl("http://www.elixir-lang.org")`
`(inets) inets_regexp.erl:80: :inets_regexp.first_match/3`
`(inets) inets_regexp.erl:68: :inets_regexp.first_match/2`
`(inets) http_uri.erl:186: :http_uri.split_uri/5`
`(inets) http_uri.erl:136: :http_uri.parse_scheme/2`
`(inets) http_uri.erl:88: :http_uri.parse/2``(inets) httpc.erl:162: :httpc.request/5`
We will cover calling Erlang libraries further along the chapter, but this is something you need to keep at the back of your head when you are dealing with certain Erlang libraries.


2.3.4        Atoms


Atoms serve as constants, something akin to Ruby's symbols. Atoms always start with a colon. There are 2 different ways to create atoms: Both
`:hello_atom`
and
`:”Hello Atom”`
are valid atoms. Atoms are *not* the same as strings, since atoms and strings are completely separate data types:


Listing 2.22: Atoms are not strings! (Interactive Elixir)

`iex> :hello_atom == "hello_atom"`
`false`
On its own, atoms are not very interesting. However, when we place atoms into *tuples*, and use them in the context of *pattern matching*, you will begin to understand the role of atoms and how Elixir exploits atoms to write declarative code. We will get to pattern matching in a few sections later. For now, let’s turn our attention to tuples.


2.3.5        Tuples


A tuple can contain different types of data. For example, a HTTP client might return a successful request in the form of a tuple such as:

`{200, “http://www.elixir-lang.org”}`
Here is how the result of an unsuccessful request might look like:

`{404, “http://www.php-is-awesome.org”}`
Tuples use zero-based access, just like how you would access array elements in most programming languages. Therefore, if you wanted the URL of the request result, you need pass in
`1`
to
`elem/2`:


Listing 2.24:  Accessing the second element in a tuple (Interactive Elixir)

`iex> elem({404, “http://www.php-is-awesome.org”}, 1)`
which will return
`http://www.php-is-awesome.org.`


You can update a tuple using
`put_elem/3`:


Listing 2.25: Updating a tuple (Interactive Elixir)

`iex> put_elem({404, “http://www.php-is-awesome.org”}, 0, 503)`
returns

`{503, "http://www.php-is-awesome.org"}`
2.3.6        Maps


Maps are essentially key-value pairs, like a hash or dictionary, depending on the language.  All map operations are exposed with the
`Map`
module.


Working with maps is pretty straightforward, with a *tiny* caveat. See if you can spot it in the examples. Let's start with an empty map:


Listing 2.26: Creating a new Map

`iex> programmers = Map.new`
`%{}`
Let's add some smart people into the map:


Listing 2.27: Adding elements to a Map

`iex> programmers = Map.put(programmers, :joe, "Erlang")`
`%{joe: "Erlang"}`

`iex> programmers = Map.put(programmers, :matz, "Ruby")`
`%{joe: "Erlang", matz: "Ruby"}`

`iex> programmers = Map.put(programmers, :rich, "Clojure")``%{joe: "Erlang", matz: "Ruby", rich: "Clojure"}`

A very important aside: Immutability



Notice how
`programmers`
is one of the arguments to
`Map.put/3`, and is *rebound* to
`programmers`
again. Why is that?

`iex> Map.put(programmers, :rasmus, "PHP")`
`%{joe: "Erlang", matz: "Ruby", rasmus: "PHP", rich: "Clojure"}`
The return value contains the new entry. Let's check the contents of
`programmers`:

`iex> programmers`
`%{joe: "Erlang", matz: "Ruby", rich: "Clojure"}`
This property is called *immutability*.


*All* data structures in Elixir are immutable, which means you cannot do any modifications to it. Any modifications you make will *always* leave the original *unchanged*. Instead, a modified copy is returned. Therefore, in order to capture the result, you can either re-bind it to the same variable name, or bind the value to another variable.



 



2.4           Guards


Let's look at
`length_converter.ex`
once more. Let’s say I want to ensure that the arguments are always numbers. Here can modify the program by adding guard clauses:


Listing 2.29: Guards added for additional checks.

`defmodule MeterToLengthConverter do`
`def convert(:feet, m) when is_number(m), do: m * 3.28084 #1`
`def convert(:inch, m) when is_number(m), do: m * 39.3701 #1`
`def convert(:yard, m) when is_number(m), do: m * 1.09361 #1``end`
#1 Guards added to the function clause.


So now, if you try something funny like
`MeterToLengthConverter.convert(:feet, “smelly”)`, none of the function clauses will match. In fact, Elixir throws a
`FunctionClauseError`:


Listing 2.30: Attempting to execute the above code results in a FunctionClauseError

`iex(1)> MeterToLengthConverter.convert (:feet, “smelly”)`
(FunctionClauseError) no function clause matching in convert/2


Negative lengths make no sense. Let’s make sure the arguments are non-negative. We can do this by adding another guard expression:


Listing 2.31:    We can include simple expressions in guards.

`defmodule MeterToLengthConverter do`
`def convert(:feet, m) when is_number(m) and m >= 0, do: m * 3.28084 #1`
`def convert(:inch, m) when is_number(m) and m >= 0, do: m * 39.3701 #1`
`def convert(:yard, m) when is_number(m) and m >= 0, do: m * 1.09361 #1``end`
#1 Check that m is a non-negative number


Besides
`is_number/1`, there are also other similar functions that will come in handy when you need to differentiate between the various data types. To generate this list, fire up
`iex`, and type
`is_`
followed by the
`<Tab>`
key.


Listing 2.32: Auto-completion in iex to discover function names (Interactive Elixir)

`iex(1)> is_`
`is_atom/1         is_binary/1       is_bitstring/1    is_boolean/1`
`is_float/1        is_function/1     is_function/2     is_integer/1`
`is_list/1         is_map/1          is_nil/1          is_number/1`
`is_pid/1          is_port/1         is_reference/1    is_tuple/1`
The
`is_*`
functions should be pretty self explanatory, except for
`is_port/1`
and
`is_reference/1`. We won’t be using ports in this book. We will meet references later on, and you will see how they are useful in giving messages a unique identity.


Guard clauses are especially useful in eliminating conditionals, and as you have guessed, useful in making sure that your arguments are of the correct type.


2.5           Pattern Matching


Pattern matching is one of the most powerful features in functional programming languages, and Elixir is no exception. In fact, pattern matching is one of my favorite features in Elixir. Once you see what pattern matching can do, you will start to yearn for it in languages that do not support them.


Elixir uses the equals operator (`=`) to perform pattern matching. Unlike most languages, Elixir not only uses the
`=`
operator for variable assignment. In fact,
`=`
is called the *match operator*. From now on, when you see a
`=`, think *matches* instead of equals. What are we matching exactly? In short, pattern matching is used to match both values and data structures. In the examples that follow, you will learn why
`=`
is called the match operator. More importantly, you will learn to love pattern matching as a powerful tool to produce beautiful code. First, let’s learn the rules:


2.5.1        = is used for assigning


The first rule of the match operator is this: Variable assignments only happen when the variable is on the *left* hand side of the expression.


Listing 2.33:  Variable assignments only occur when the variable is on the left. (Interactive Elixir)

`iex> programmers = Map.put(programmers, :jose, "Elixir")`
Will result in:

`%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
Here, we assignment the result of
`Map.put/2`
into
`programmers`. As expected,
`programmers`
contains:

`iex> programmers`
`%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
2.5.2        = is also used for matching


Here is when things get slightly interesting. Let’s swap the order of the previous expression we had:


Listing 2.34: Matching the map (on the left) with
`programmers`
(Interactive Elixir)

`iex> %{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"} = programmers`
`%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
Here, we flipped things around. Notice how this is *not* an assignment. Instead, a *successful pattern match* has occurred, because the contents of both the left hand side and
`programmers`
are identical. Let's see an *unsuccessful* pattern match:


Listing 2.35:  An unsuccessful pattern match (Interactive Elixir)

`iex> %{tolkien: "Elvish"} = programmers`
`** (MatchError) no match of right hand side value: %{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
When an unsuccessful match occurs, a
`MatchError`
is raised. Let’s take a look at destructuring next, because we will need this in order to perform some cool tricks with pattern matching.


2.5.3        Destructuring


Destructuring is where pattern matching really shines. One of the nicest definitions of destructuring comes from *Common Lisp the Language*[[2]](#ugUVMuBAS4AjXQEz6xpJmzG):


Destructuring allows you to *bind a set of variables* to a corresponding *set of values* anywhere that you can normally bind a value to a single variable.


Here is what it means in code:


Listing 2.36: Binding variables on the left to values on the right (Interactive Elixir)

`iex> %{joe: a, jose: b, matz: c, rich: d} =`
`%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}``%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
Here are the contents of each of the variables:

`iex> a`
`"Erlang"`

`iex> b`
`"Elixir"`

`iex> c`
`"Ruby"`

`iex> d``"Clojure"`
Here, we bind a set of *variables* (`a`,
`b`,
`c`
and
`d)`
to a corresponding set of *values* (`“Erlang”`,
`“Elixir”`,
`“Ruby”`
and
`“Clojure”`). What if you were only interested in extracting some of the information? No problem, because you can do pattern-matching without needing to specify the entire pattern:


Listing 2.37:  Matching only part of a pattern. (Interactive Elixir)

`iex> %{jose: most_awesome_language} = programmers`
`%{joe: "Erlang", jose: "Elixir", matz: "Ruby", rich: "Clojure"}`
`iex> most_awesome_language``"Elixir"`
This will come in very handy when you are only interesting in extracting a few pieces of information. Here is another useful technique that is used very often in Elixir programs. Notice the return values of these two expressions:


Listing 2.38: A successful fetch returns
`{:ok, value}`
(Interactive Elixir)

`iex> Map.fetch(programmers, :rich)`
`{:ok, "Clojure"}`
Listing 2.39: An unsuccessful fetch returns
`:error`
(Interactive Elixir)

`iex> Map.fetch(programmers, :rasmus)`
`:error`
Notice that a tuple with the atom
`:ok`
and the value is returned when a key is found, and an
`:error`
atom otherwise. Here you will see how tuples and atoms are useful, and how we can exploit this with pattern matching. By making use of the return values of both the happy and the exceptional path, we can express ourselves like so:


Listing 2.40:   Handling both the happy path and error path (Interactive Elixir)

`iex> case Map.fetch(programmers, :rich) do #1`
`...>   {:ok, language} ->`
`...>     IO.puts "#{language} is a legit language."`
`...>   :error ->`
`...>     IO.puts "No idea what language this is."``...> end`
This returns:

`Clojure is a legit language.`
Example: Reading a File


This technique is very useful for declaring preconditions in your program. What do I mean by that? Let’s take reading a file as an example. If most of your logic depends on the file being *readable*, then it makes sense to know as soon as possible if some error occurs with file reading. It would be helpful to know what kind of error occurred too. Here’s a snippet from the
`File.read/1`
documentation:


![](../images//2_6.png)  



Figure 2.6 Documentation for File.read/1


How would you write the file reading portion? More importantly, what can we learn from reading the above documentation?


1.  For a successful read,
`File.read/1`
returns a
`{:ok, binary}`
tuple. Note that
`binary`
is the entire contents of the read file.


2.  Otherwise, a
`{:error, posix}`
tuple will be returned. The variable
`posix`
contains the error reasons, which is an atom such as
`:enoent`
or
`:eaccess`.


Listing 2.41:  Reading a file

`case File.read("KISS - Beth.mp3") do`
`{:ok, binary} ->`
`IO.puts "KIϟϟ rocks!"`
`{:error, reason} ->`
`IO.puts "No Rock N Roll for anyone today because of #{reason}."``end`
Example: Tic-Tac-Toe board


Here's an illustrative example from the Tic-Tac-Toe application that uses tuples. In this example, we have a
`check_board/1`
function that checks against a tic-tac-toe’s board configuration. The board is expressed using tuples. Notice how we “draw” the board using tuples, and how easy to understand the code is:

`def check_board(board) do`
`case board do`
`{ :x, :x, :x,`
`_ , _ , _ ,`
`_ , _ , _ } -> :x_win`

`{ _ , _ , _ ,`
`:x, :x, :x,`
`_ , _ , _ } -> :x_win`

`{ _ , _ , _ ,`
`_ , _ , _ ,`
`:x, :x, :x} -> :x_win`

`{ :x, _ , _ ,`
`:x, _ , _ ,`
`:x, _ , _ } -> :x_win`

`{ _ , :x, _ ,`
`_ , :x, _ ,`
`_ , :x, _ } -> :x_win`

`{ _ , _ , :x,`
`_ , _ , :x,`
`_ , _ , :x} -> :x_win`

`{ :x, _ , _ ,`
`_ , :x, _ ,`
`_ , _ , :x} -> :x_win`

`{ _ , _ , :x,`
`_ , :x, _ ,`
`:x, _ , _ } -> :x_win`

`# Player O board patterns omitted ...`

`{ a, b, c,`
`d, e, f,`
`g, h, i } when a and b and c and d and e and f and g and h and i -> :draw`

`_ -> :in_progress`

`end``end`
The '`_`' is the "don't care" or "match everything" operator. You will see quite a few examples in this book. You will see more pattern-matching in the next section, where we look at *lists*.


Example: Parsing an MP3 file


Elixir is brilliant for parsing binary data. In this example, we are going to extract metadata from an MP3 file. It is also a good exercise to reinforce some of the concepts you have learnt earlier. Before you parse any binary, you must know the layout. The information that we are interested in, the *ID3 tag*, is located at the *last 128 bytes* of the mp3 binary:


![](../images//2_7.png)  



Figure 2.7: The ID3 tag is located at the last 128 bytes of the MP3 binary.


This means that we must somehow ignore the audio data portion, and concentrate only on the ID3 tag. The following diagram shows the layout of the ID3 tag:


![](../images//2_8.png)  



Figure 2.8: The layout of the ID3 tag.


The first 3 bytes of the ID3 tag is called the header, and contains 3 characters – “T”, “A”, and a “G”. The next 30 bytes contain the *title*. The next 30 bytes is the *artist*, followed by another 30 bytes containing the *album*. The next 4 bytes is the *year* (e.g.: “2”, “0”, “1”, “4”). Try to imagine how you might attempt this in some other programming language. Here is the Elixir version. Save this file as
`id3.ex`.


Listing 2.42:  The full ID3 parsing program. Save this file as
`id3.ex`.

`defmodule ID3Parser do`

`def parse(file_name) do`
`case File.read(file_name) do                                         #1`

`{:ok, mp3} ->                                                      #2`
`mp3_byte_size = byte_size(mp3) – 128                             #4`

`<< _ :: binary-size(mp3_byte_size), id3_tag :: binary >> = mp3   #5`

`<< "TAG", title   :: binary-size(30),`
`artist  :: binary-size(30),`
`album   :: binary-size(30),`
`year    :: binary-size(4),`
`_rest   :: binary >>       = id3_tag                   #6`

`IO.puts "#{artist} - #{title} (#{album}, #{year})"`

`_ ->                                                               #3`
`IO.puts "Couldn't open #{file_name}"`
`end`
`end``end`
#1 Read the MP3 binary.


#2 A successful file read returns a tuple that matches this pattern


#3 A failed file read is matched with anything else


#4 Calculate the audio portion of the MP3 in bytes


#5 Pattern matching the MP3 binary to capture the bytes of the ID3 tag


#6 Pattern matching the ID3 tag to capture the various ID3 fields


An example run of the program:

`% iex id3.ex`
`iex(1)> ID3Parser.parse "sample.mp3"`
And an example result:

`Lana Del Rey - Ultraviolence (Ultraviolence, 2014)`
`:ok`
Let’s walk through the program. First, the program reads the MP3 binary. A happy path will return a tuple that matches
`{:ok, mp3}`, where
`mp3`
contains the binary contents of the file. Otherwise, the “catch-all” \_ operator will match a failed file read.


Since we are interested only in the ID3 tag, we need to find a way to “skip ahead”. We first compute *size in bytes* of the *audio* portion of the binary. Now that we have this information, we can make use of the size of the audio portion to tell Elixir how to destructure the binary. We pattern match the MP3 binary by declaring a pattern on the left, and the mp3 variable on the right. Recall that variable assignments are on the left, and pattern matching is attempted otherwise.


![](../images//2_9.png)  



Figure 2.9: How the binary gets destructured.


You might recognize the
`<< >>.`
It is used to represent a binary. We then declare that we are not interested in the audio part. How? We do that by specify the binary size that we have computed previously. What *remains*, is the ID3 tag. That is captured in the
`id3_tag`
variable. Now we are free to extract the information from the ID3 tag!


In order to do that, we perform another pattern match with the declared pattern on the left and
`id3_tag`
on the right. By declaring the appropriate number of bytes, the title, artist and other information is captured in the respective variables.


![](../images//2_10.png)  



Figure 2.10: Destructuring the ID3 binary.


2.6           Lists


Lists are another data type in Elixir. There are quite a few interesting things you can do with lists, and therefore deserves its own section. Lists are somewhat similar to *linked-lists*[[3]](#uVViRxNwYGTYar6izeVraFD) in that random access is essentially a O(n) (linear) operation. Here is the definition of a list:


A non-empty list consists of a head and a tail. The tail is also a list.


Notice the recursive nature of the above definition. Translated to code:

`iex> [1, 2, 3] == [1 | [2 | [3 | []]]]`
`true`
A diagram might illustrate this better:    


![](../images//2_11.png)  



Figure 2.11: [1,2,3] represented as a picture


Let’s try to understand this picture by starting at the outermost box. This says that the head of the list is 1, followed by the tail of the list. This tail, in turn, is yet another list. This time, the head of this list is 2, followed by the tail, which (again) is another list.


Finally, this list (from the third enclosing box) consists of a head of 3, and a tail. This tail is an empty list. In fact, the *tail of the final element of any list is always an empty list*. Recursive functions make use of this fact to determine when the end of the list is reached.


You can also use the pattern-matching operator to prove that both sides are in fact the same thing :


Listing 2.43: The left hand side and right hand side is equivalent. (Interactive Elixir)

`iex> [1, 2, 3] = [1 | [2 | [3 | []]]]`
`[1, 2, 3]`
Since no
`MatchError`
occurred, we can be certain that both representations of the list are equivalent. Of course, you wouldn’t be typing
`[1|[2|[3|[]]]]`
in your day-to-day code. This is just to emphasize that a list is a recursive data structure.


I have not explained what ‘`|`’ is. The ‘`|`’ operator is commonly called the *cons* [[4]](#uFTSC7YFSH3DxvWmebI7ae2)operator. When applied to lists, it separates the head and tail. That is, the list is *destructured*. This is yet another instance of pattern matching in action.


Listing 2.44: Destructuring a list using the cons operator. (Interactive Elixir)

`iex> [head | tail] = [1, 2, 3]`
`[1, 2, 3]`
Let’s check the contents of head and tail:

`iex> head`
`1`
`iex> tail #A``[2, 3]`
#A This is also a list


Notice that
`tail`
is also a list, which is in line with the definition. You can also use the cons operator to *add* (or append) to the beginning of a list:


Listing 2.45: Using the cons operator to append to a list. (Interactive Elixir)

`iex(1)> list = [1, 2, 3]`
`[1, 2, 3]`
`iex(2)> [0 | list ]``[0, 1, 2, 3]`
Listing 2.46: Using the ++ operator to concatenate lists (Interactive Elixir)


We can also use the
`++`
operator to concatenate lists:

`iex(3)> [0] ++ [1, 2, 3]`
`[0, 1, 2, 3]`
What about a single element list? If you understood the diagram of the list previously, then this would be a piece of cake.


Listing 2.47: The tail of a single element list matches to an empty list. (Interactive Elixir)

`iex(1)> [ head | tail ] = [:lonely]`
`[:lonely]`
`iex(2)> head`
`:lonely`
`iex(3)> tail``[]`
The list we have here contains a single atom. Now notice our
`tail`
is an empty list. This might seem strange at first, but if you think about it, it fits the definition. It is precisely this definition that allows us to do interesting things with lists and recursion, which we examine next.


Example: Flattening a List


Now that you know how lists work, let's build our very own
`flatten/1`.
`flatten/1`
takes in a possibly nested list and returns a flattened version. Flattening lists can be useful especially if the list is used to represent a Tree [[5]](#u2to24Ap2mk93kr7NvjAZIG)data structure. Flattening the tree therefore returns all the elements contained in the tree. Let’s see an example:

`List.flatten [1, [:two], ["three", []]]`
will return

`[1, :two, "three"]`
Here is one possible implementation of
`flatten/1`:

`defmodule MyList do`
`def flatten([]), do: [] #1`

`def flatten([ head | tail ]) do  #2`
`flatten(head) ++ flatten(tail) #2`
`end`

`def flatten(head), do: [ head ] #3``end`
#1 Base case, an empty list


#2 Non-empty list, with more than 1 element


#3 Single element list


Take a moment to digest the code, because there's more than meets the eye. There are 3 cases to consider:


We begin with the base case (or degenerate case if you've done some CS course) – the empty list. If we get the empty list, we simply return an empty list.


For a non-empty list #2, we use the cons operator to split into the
`head`
and
`tail`. We then recursively call
`flatten/1`
on both the
`head`
and
`tail.`
Next, the result is concatenated using the
`++`
operator. Note that
`head`
can also be a nested list. For example,
`[[1], 2]`
would mean that
`head`
is
`[1]`.


If we get a non-list argument, we turn it into a list. Now, consider (it helps to trace this on paper) what happens to a list such as
`[[1], 2]`. Let's trace the execution:


1.   The first function clause #1 does not match.


2.  The second function clause #2 matches though. In this case, we pattern match the list, and
`head`
is
`[1]`, and
`tail`
is
`2`. Now,
`flatten([1])`
and
`flatten(2)`
are called recursively.


3.  Let's handle
`flatten([1])`. Again it does not match the first clause #1. The second one #2 matches.  `head`
 is
`1`, and
`tail`
is
`[]`.


4.  Now,
`flatten(1)`
is called, and now, the third function clause #3 matches, and returns
`[1]`.
`flatten([])`
matches the first clause and returns
`[]`. A previous call to
`flatten(2)`
(see step 2) returns
`[2]`.
`[1] ++ [] ++ [2]`
yields our flattened list.


Don't despair if you did not get that the first time round. As with most things, some practice will go a long way. Also, you will see numerous examples in the upcoming chapters.


Ordering of Function Clauses


I previously mentioned that the *order* of function clauses matter. This is a perfect place to explain why:


Listing 2.11:  The order of function clauses matter!

`defmodule MyList do`

`def flatten([ head | tail ]) do`
`flatten(head) ++ flatten(tail)`
`end`

`def flatten(head), do: [ head ]`

`def flatten([]), do: [] #1`
`end`
#1 This line never runs!


We have made the base case the last clause. Think about what happens when we try
`MyList.flatten([])`? We expect to get
`[]`, but in fact we get back
`[[]]`. If you give it a little thought, you will realize that #1 never runs. The reason is that the second function clause will match
`[]`, and therefore the third function clause will be ignored.


Let's try running this for real:


Listing 2.12: Elixir helpfully warns about unmatched clauses. (Interactive Elixir)

`% iex length_converter.ex`
`warning: this clause cannot match because a previous clause at``line 7 always matches`
Elixir has got our back! Take heed of warnings like this, because they can save you hours of debugging headaches. And unmatched clauses could either mean dead code, or in the worse case, an infinite loop.


2.7           Meet |>, the Pipe operator


Now, I would like introduce one of the most useful operators ever invented in Programming Language History™ –
`|>`[[6]](#uK9hrHa3kQCIGQ7flXO8FoF). The
`|>`
takes the result of the expression on the left and inserts it as the first parameter of the function call on the right. Here is a code snippet from an Elixir program I have written recently. Without the pipe operator, this is how I would have written it:


Listing 2.48: Without the |> operator (or, how most languages would do it)

`defmodule URLWorker do`
`def start(url) do`
`do_request(HTTPoison.get(url))`
`end`
`# ...``end`
`HTTPoison`
is a HTTP client. It takes in a
`url`
and returns the HTML page. The page is then passed to the
`do_request`
function to perform some parsing. Notice that in this version, you have to look for the innermost brackets to locate
`url`, then move outwards as you mentally trace the successive function calls.


I present you the version with pipe operators:


Listing 2.49: With the |> operator

`defmodule URLWorker do`
`def start(url) do`
`result = url |> HTTPoison.get |> do_request`
`end`
`# ...``end`
No contest right? Many of the examples will make extensive use of
`|>`. The more you use
`|>`, the more you will start to see *data as being* *transformed* from one form to another, something like an assembly line. In fact, once you use it often enough, you will start miss it when you program in other languages.


Example: Filtering files by filename in a directory


Let’s say I have a directory filled with e-books, where this directory could be nested with folders. I want to get the file names of only the EPUBs. That is, I only want books that have filenames that end with
`*.epub`, with “Java” in it. Here’s how I would do it:


Listing 2.50: Filtering epubs that have “Java” in them.

`"/Users/Ben/Books"                                    #1`
`|> Path.join("**/*.epub")                           #2`
`|> Path.wildcard                                    #3`
`|> Enum.filter(fn fname ->                          #4`
`String.contains?(Path.basename(fname), "Java")``end)`
An example output looks like:


Listing 2.51: An example output of the above expression

`["/Users/Ben/Books/Java/Java_Concurrency_In_Practice.epub",`
`"/Users/Ben/Books/Javascript/JavaScript Patterns.epub",`
`"/Users/Ben/Books/Javascript/Functional_JavaScript.epub",``"/Users/Ben/Books/Ruby/Using_JRuby_Bringing_Ruby_to_Java.epub"]`
#1 is the string representation of the directory. In #2, we construct a path with wildcards. Additionally, we specify that we are only interested in EPUBs. The result of this is passed into #3. The wildcard function reads the path, and returns a list of matched file names. This in turn is passed into the filter function in #4, where only file names containing “Java” is selected. It is very nice to read code that describes its steps so explicitly and obvious.


2.8           Erlang Interoperability


Because both Elixir and Erlang share the same byte code, calling Erlang code does not affect performance in any way. More importantly, this means that you are free to use *any* Erlang library out there with your Elixir code.


Calling Erlang functions from Elixir


The only caveat is *how* the code is called. For example, you could generate a random number in Erlang like so:


Listing 2.52: Generating a random number in Erlang (Interactive Erlang)

`1> random:uniform(123)`
`55`
This function comes as part of the standard Erlang distribution. I could invoke the same Erlang function in Elixir, with some syntactical tweaks:


Listing 2.53:  Translating 
`random:uniform().`to Elixir (Interactive Elixir) 

`iex> :random.uniform(123)`
`55`
Notice the positions of the colon and dot between the two listings. That’s really all to it! There is a minor caveat in Elixir when working with native Erlang functions. You cannot access documentation for Erlang functions from
`iex`:


Listing 2.54:  Erlang documentation is not available in iex (Interactive Elixir)

`iex(3)> h :random`
`:random is an Erlang module and, as such, it does not have Elixir-style docs`
Calling Erlang functions can be very useful when Elixir doesn’t have an implementation available in the standard library. If you compare the Erlang standard library and the Elixir one, you might draw the conclusion that Erlang’s library is much more feature packed. But if you think about it, Elixir gets everything for free!


Calling the Erlang HTTP client in Elixir


Usually if I find that Elixir is missing a certain feature I want, I will usually check if there’s an Erlang standard library function that I can use first, before searching for third party libraries. For example, I once wanted to build a web crawler in Elixir. One of the very first steps to building a web crawler is to be able to download a web page. This requires a HTTP client. Elixir doesn’t come with a built-in HTTP client – it doesn’t need to, because Erlang comes with one, aptly named
`httpc`[[7]](#ugLW5GzsQcZ8zXABeWVTc2H). 


Let’s say I want to download the web page of a certain programming language. I go to the Erlang documentation[[8]](#u2nrvV8vG6J5gy7FjyByQX2), and I manage to find exactly what I need:


![](../images//2_6a.png)  



Figure 2.6  The httpc:request/1 Erlang documentation


First, I need to start the
`inets`
application (it is stated in the documentation), followed by the actual request:


Listing 2.55: Downloading a web page, using Erlang’s httpc library (Interactive Elixir)

`iex(1)> :inets.start`
`:ok`
`iex(2)> {:ok, {status, headers, body}} = :httpc.request 'http://www.elixir-lang.org'`
`{:ok,`
`{{'HTTP/1.1', 200, 'OK'},`
`[{'cache-control', 'max-age=600'}, {'date', 'Tue, 28 Oct 2014 16:17:24 GMT'},`
`{'accept-ranges', 'bytes'}, {'server', 'GitHub.com'},`
`{'vary', 'Accept-Encoding'}, {'content-length', '17251'},`
`{'content-type', 'text/html; charset=utf-8'},`
`{'expires', 'Tue, 28 Oct 2014 16:27:24 GMT'},`
`{'last-modified', 'Tue, 21 Oct 2014 23:38:22 GMT'}],`
`[60, 33, 68, 79, 67, 84, 89, 80, 69, 32, 104, 116, 109, 108, 62, 10, 60, 104,`
`116, 109, 108, 32, 120, 109, 108, 110, 115, 61, 34, 104, 116, 116, 112, 58,``47, 47, 119, 119, 119, 46, 119, 51, 46, 111, 114, 103, 47, 49, 57, 57, ...]}}`
And one more thing …


Erlang has also a very neat GUI frontend called *Observer* that let’s you inspect the Erlang virtual machine, among other things. Invoking it is simple:


Listing 2.56:  Invoking Observer, a built-in Erlang tool (Interactive Elixir)

`iex(1)> :observer.start`
Since you are not running any computationally intensive processes, you won’t be seeing much action for now. But here’s a few screenshots to whet your appetite:


![](../images//2_7a.png)  



Figure 2.7 Screenshots from Observer


Observer is very useful when it comes to seeing how much load the VM is taking, the layout of your supervision trees (you will learn about that in the later chapters), and also looking at the data stored in the built-in database(s) that Erlang provides.


2.9           Exercises


This was a pretty long chapter. Now it’s time to make sure you understood everything in the chapter.


1.   Implement
`sum/1`. This function should take in a list of numbers, and return the sum of the list.


2.  Explore the
`Enum`
module.


3.  Transform
`[1,[[2],3]]`
to
`[9, 4, 1]`
with and without the pipe operator.


4.  Translate
`crypto:md5("Tales from the Crypt").`
from Erlang to Elixir.


5.  Explore the official Elixir "Getting Started" guide[[9]](#uzWboseQ5tC5ZfAHC6pfKpA).


6.  Take a look at an IPV4 packet. Try writing a parser for that.


2.10       Summary


This concludes our whirlwind tour. If you have made it this far, give yourself a pat on the shoulder. Do not worry if you have not understood everything. Many of the concepts will make sense along the way, and many of the programming constructs will be obvious once you see its applications. As a quick recap, here is what we just learnt about:


·      Elixir’s fundamental data types.


·      Guards, and how they work nicely together with function clauses.


·      Pattern matching, and how it leads to very declarative code. We’ve also looked at a few real-world examples of pattern matching.


·      Lists, another fundamental data structure. We’ve also seen how lists are represented internally in Elixir, and how that facilitates recursion.


·      How Elixir and Erlang plays nicely with each other.


In the next chapter, we learn the fundamental unit of concurrency in Elixir – the process. This is one of the features that make Elixir vastly different from “traditional” programming languages.





[****[1]****](#uGqF9oefXSN254ifO9nOI74) https://github.com/tonini/alchemist.el




[****[2]****](#uoUcCmRNSIi5gGo5YytDiK9) http://www.cs.cmu.edu/Groups/AI/html/cltl/clm/node252.html




[****[3]****](#usLiHAmBCCcYO4nRXGgIKQB) http://en.wikipedia.org/wiki/Linked\_list




[****[4]****](#uF8QOmDRZNNvpCpSmjAEfs5) This is short for construct. See <http://en.wikipedia.org/wiki/Cons> for more information.




[****[5]****](#uD2AVQHJ9OMdJBNJCWxC9tB) http://en.wikipedia.org/wiki/Tree\_%28data\_structure%29#Representations




[****[6]****](#udkkAPdyHmLgLsDveAOujJ9) Little trivia – The |> operator is inspired from F#.




[****[7]****](#uJJ86MqDQDsHISshMOe2s83) http://erlang.org/doc/man/httpc.html#request-1




[****[8]****](#uDMzs6Wh684M5CCzxbJmcyE) Who am I kidding? In reality, I’ll probably land on Stack Overflow first.




[****[9]****](#uYiNVPWCvsaM73aAlVYO2y7) http://elixir-lang.org/getting\_started/1.html





