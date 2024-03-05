""" 
    该脚本用于格式化Elixir代码段
    1. 遍历所有的.tex文件
    2. 使用正则表达式找到所有的Elixir代码段
    3. 调用mix format格式化Elixir代码
    4. 用格式化后的代码替换原始代码
    5. 保存文件
"""

import re
import subprocess
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor


def format_elixir_code(match):
    # 对每个找到的代码段进行格式化
    code = match.group(1).strip()
    # 保存到临时文件
    temp_file_path = f'temp_{uuid.uuid4()}.ex'
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(code)
    # 调用mix format格式化Elixir代码
    subprocess.run(['mix', 'format', temp_file_path])
    # 读取格式化后的代码
    with open(temp_file_path, 'r') as temp_file:
        formatted_code = temp_file.read()
        
    # 删除临时文件
    subprocess.run(['rm', temp_file_path])
    # 返回新的代码段
    return '\\begin{minted}[linenos]{elixir}\n' + formatted_code + '\\end{minted}'

def get_all_texs(tex_file_dir=None):
    if tex_file_dir is None:
        tex_file_dir = Path(__file__).parent.parent / 'contents'
    # 初始化一个空列表来存储找到的所有.tex文件路径
    tex_files = []
    # 遍历tex_file_dir目录及其所有子目录，寻找.tex文件
    for tex_file in tex_file_dir.rglob('*.tex'):
        tex_files.append(tex_file)
    return tex_files

def format_file(tex_file):
    # 读取.tex文件
    with open(tex_file, 'r') as file:
        content = file.read()

    pattern = re.compile(r'\\begin{minted}\[linenos\]{elixir}\n(.*?)\\end{minted}', re.DOTALL)
    # 替换原始文件中的所有Elixir代码段
    formatted_content = re.sub(pattern, format_elixir_code, content)

    # 将格式化后的内容写回文件
    with open(tex_file, 'w') as file:
        file.write(formatted_content)
    
    print(f'Formatted {tex_file}')
    
if __name__ == '__main__':
    # 文件路径
    tex_files = get_all_texs()
    # 使用ThreadPoolExecutor并行处理所有文件
    with ThreadPoolExecutor() as executor:
        executor.map(format_file, tex_files)


