#!/usr/bin/env python3

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "gitpython",
#   "tqdm",
#   "transformers",
#   "rich",
# ]
# ///

import os
import sys
import shutil
import tempfile
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

# Set environment variable to suppress transformers warnings
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

from git import Repo
from tqdm import tqdm
from transformers import AutoTokenizer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint

# Initialize the console and tokenizer
warnings.filterwarnings('ignore')
console = Console()
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# File extensions mapped to their technologies
FILE_EXTENSIONS = {
    # Python and related
    '.py': 'Python',
    '.pyi': 'Python Interface',
    '.pyx': 'Cython',
    '.pxd': 'Cython Header',
    '.ipynb': 'Jupyter Notebook',
    '.requirements.txt': 'Python Requirements',
    '.pipfile': 'Python Pipenv',
    '.pyproject.toml': 'Python Project',
    '.txt': 'Plain Text',
    '.md': 'Markdown',

    # Web Technologies
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SASS',
    '.sass': 'SASS',
    '.less': 'LESS',
    '.js': 'JavaScript',
    '.jsx': 'React JSX',
    '.ts': 'TypeScript',
    '.tsx': 'React TSX',
    '.vue': 'Vue.js',
    '.svelte': 'Svelte',
    '.php': 'PHP',
    '.blade.php': 'Laravel Blade',
    '.hbs': 'Handlebars',
    '.ejs': 'EJS Template',
    '.astro': 'Astro',

    # System Programming
    '.c': 'C',
    '.h': 'C Header',
    '.cpp': 'C++',
    '.hpp': 'C++ Header',
    '.cc': 'C++',
    '.hh': 'C++ Header',
    '.cxx': 'C++',
    '.rs': 'Rust',
    '.go': 'Go',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',

    # JVM Languages
    '.java': 'Java',
    '.class': 'Java Bytecode',
    '.jar': 'Java Archive',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin Script',
    '.groovy': 'Groovy',
    '.scala': 'Scala',
    '.clj': 'Clojure',

    # .NET Languages
    '.cs': 'C#',
    '.vb': 'Visual Basic',
    '.fs': 'F#',
    '.fsx': 'F# Script',
    '.xaml': 'XAML',

    # Shell and Scripts
    '.sh': 'Shell Script',
    '.bash': 'Bash Script',
    '.zsh': 'Zsh Script',
    '.fish': 'Fish Script',
    '.ps1': 'PowerShell',
    '.bat': 'Batch File',
    '.cmd': 'Windows Command',
    '.nu': 'Nushell Script',

    # Ruby and Related
    '.rb': 'Ruby',
    '.erb': 'Ruby ERB Template',
    '.rake': 'Ruby Rake',
    '.gemspec': 'Ruby Gem Spec',

    # Other Programming Languages
    '.pl': 'Perl',
    '.pm': 'Perl Module',
    '.ex': 'Elixir',
    '.exs': 'Elixir Script',
    '.erl': 'Erlang',
    '.hrl': 'Erlang Header',
    '.hs': 'Haskell',
    '.lhs': 'Literate Haskell',
    '.hcl': 'HCL (Terraform)',
    '.lua': 'Lua',
    '.r': 'R',
    '.rmd': 'R Markdown',
    '.jl': 'Julia',
    '.dart': 'Dart',
    '.nim': 'Nim',
    '.ml': 'OCaml',
    '.mli': 'OCaml Interface',

    # Configuration and Data
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.conf': 'Configuration',
    '.config': 'Configuration',
    '.env': 'Environment Variables',
    '.properties': 'Properties',
    '.xml': 'XML',
    '.xsd': 'XML Schema',
    '.dtd': 'Document Type Definition',
    '.csv': 'CSV',
    '.tsv': 'TSV',

    # Documentation and Text
    '.md': 'Markdown',
    '.mdx': 'MDX',
    '.rst': 'reStructuredText',
    '.txt': 'Plain Text',
    '.tex': 'LaTeX',
    '.adoc': 'AsciiDoc',
    '.wiki': 'Wiki Markup',
    '.org': 'Org Mode',

    # Database
    '.sql': 'SQL',
    '.psql': 'PostgreSQL',
    '.plsql': 'PL/SQL',
    '.tsql': 'T-SQL',
    '.prisma': 'Prisma Schema',

    # Build and Package
    '.gradle': 'Gradle',
    '.maven': 'Maven POM',
    '.cmake': 'CMake',
    '.make': 'Makefile',
    '.dockerfile': 'Dockerfile',
    '.containerfile': 'Container File',
    '.nix': 'Nix Expression',

    # Web Assembly
    '.wat': 'WebAssembly Text',
    '.wasm': 'WebAssembly Binary',

    # GraphQL
    '.graphql': 'GraphQL',
    '.gql': 'GraphQL',

    # Protocol Buffers and gRPC
    '.proto': 'Protocol Buffers',

    # Mobile Development
    '.xcodeproj': 'Xcode Project',
    '.pbxproj': 'Xcode Project',
    '.gradle': 'Android Gradle',
    '.plist': 'Property List',

    # Game Development
    '.unity': 'Unity Scene',
    '.prefab': 'Unity Prefab',
    '.godot': 'Godot Resource',
    '.tscn': 'Godot Scene',

    # AI/ML
    '.onnx': 'ONNX Model',
    '.h5': 'HDF5 Model',
    '.pkl': 'Pickle Model',
    '.model': 'Model File',
}

# Set of all text extensions for quick lookup
TEXT_EXTENSIONS = set(FILE_EXTENSIONS.keys())

def is_binary(file_path: str) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.read(1024)
            return False
    except UnicodeDecodeError:
        return True

def count_tokens(content: str) -> int:
    """Count tokens in the given content using GPT-2 tokenizer."""
    return len(tokenizer.encode(content))

def format_number(num: int) -> str:
    """Format a number with thousands separator and appropriate suffix."""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    return f"{num:,}"

def process_repository(repo_path: str, total_only: bool = False) -> Tuple[int, Dict[str, int], Dict[str, int]]:
    """Process all files in the repository and count tokens."""
    total_tokens = 0
    extension_stats = {}
    file_counts = {}

    # Define directories to exclude
    exclude_dirs = {'.git', 'venv', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache'}

    # Get list of all files
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            if extension in FILE_EXTENSIONS and not is_binary(file_path):
                all_files.append((file_path, extension))
                file_counts[extension] = file_counts.get(extension, 0) + 1

    # Process files
    for file_path, extension in (track(all_files, description="[bold blue]Processing files") if not total_only else all_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tokens = count_tokens(content)
                total_tokens += tokens
                if extension not in extension_stats:
                    extension_stats[extension] = tokens
                else:
                    extension_stats[extension] += tokens
        except Exception as e:
            if not total_only:
                console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")

    return total_tokens, extension_stats, file_counts

def main():
    # Check for correct number of arguments
    if len(sys.argv) < 2:
        console.print("[red]Usage: token-counter <repository_url_or_path> [-total][/red]")
        sys.exit(1)
        
    # Check for -total flag
    total_only = "-total" in sys.argv
    target = sys.argv[1] if sys.argv[1] != "-total" else sys.argv[2]
    
    # Suppress all warnings if total_only is True
    if total_only:
        import logging
        logging.getLogger('transformers').setLevel(logging.ERROR)

    temp_dir = None

    # Check if the target is a local directory
    if os.path.isdir(target):
        if not total_only:
            console.print(f"[green]Analyzing local directory: {target}[/green]")
        analyze_path = target
    else:
        # Clone the repository to a temporary directory
        temp_dir = tempfile.mkdtemp()
        if not total_only:
            console.print(f"[yellow]Cloning repository: {target}[/yellow]")
        try:
            Repo.clone_from(target, temp_dir)
            analyze_path = temp_dir
        except Exception as e:
            console.print(f"[red]Error cloning repository: {str(e)}[/red]")
            shutil.rmtree(temp_dir)
            sys.exit(1)

    try:
        total_tokens, extension_stats, file_counts = process_repository(analyze_path, total_only)
    except Exception as e:
        if not total_only:
            console.print(f"[red]Error analyzing repository: {str(e)}[/red]")
        if temp_dir:
            shutil.rmtree(temp_dir)
        sys.exit(1)

    # Print results
    if total_only:
        # Only print the total number
        print(total_tokens)
    else:
        console.print("\n[bold cyan]Results:[/bold cyan]")
        console.print(f"Total tokens: [green]{format_number(total_tokens)}[/green] ({total_tokens:,})")

    if not total_only:
        # Create and populate extension table
        ext_table = Table(title="\n[bold]Tokens by file extension[/bold]")
        ext_table.add_column("Extension", style="cyan")
        ext_table.add_column("Tokens", justify="right", style="green")
        ext_table.add_column("Files", justify="right", style="yellow")

        for ext, count in sorted(extension_stats.items(), key=lambda x: x[1], reverse=True):
            ext_table.add_row(
                ext,
                f"{format_number(count)} ({count:,})",
                f"{file_counts[ext]} file{'s' if file_counts[ext] != 1 else ''}"
            )
        console.print(ext_table)

        # Group results by technology category
        tech_stats = {}
        tech_file_counts = {}
        for ext, count in extension_stats.items():
            tech = FILE_EXTENSIONS[ext]
            tech_stats[tech] = tech_stats.get(tech, 0) + count
            tech_file_counts[tech] = tech_file_counts.get(tech, 0) + file_counts[ext]

        # Create and populate technology table
        tech_table = Table(title="\n[bold]Tokens by Technology[/bold]")
        tech_table.add_column("Technology", style="magenta")
        tech_table.add_column("Tokens", justify="right", style="green")
        tech_table.add_column("Files", justify="right", style="yellow")

        for tech, count in sorted(tech_stats.items(), key=lambda x: x[1], reverse=True):
            tech_table.add_row(
                tech,
                f"{format_number(count)} ({count:,})",
                f"{tech_file_counts[tech]} file{'s' if tech_file_counts[tech] != 1 else ''}"
            )
        console.print(tech_table)

        # Create and populate context window table
        windows = {
            # OpenAI Models
            "GPT-3.5 (4K)": 4096,
            "GPT-4 (8K)": 8192,
            "GPT-4 (32K)": 32768,
            "GPT-4 Turbo (128K)": 128000,

            # Anthropic Models
            "Claude 2 (100K)": 100000,
            "Claude 3 Opus (200K)": 200000,
            "Claude 3 Sonnet (200K)": 200000,
            "Claude 3 Haiku (200K)": 200000,

            # Google Models
            "Gemini Pro (32K)": 32768,
            "PaLM 2 (8K)": 8192,

            # Meta Models
            "Llama 2 (4K)": 4096,
            "Code Llama (100K)": 100000,

            # Other Models
            "Mistral Large (32K)": 32768,
            "Mixtral 8x7B (32K)": 32768,
            "Yi-34B (200K)": 200000,
            "Cohere Command (128K)": 128000,
        }

        context_table = Table(title="\n[bold]Context Window Comparisons[/bold]")
        context_table.add_column("Model", style="blue")
        context_table.add_column("Context Usage", justify="right")

        for model, window in windows.items():
            percentage = (total_tokens / window) * 100
            color = "red" if percentage > 100 else "green"
            context_table.add_row(model, f"[{color}]{percentage:.1f}%[/{color}]")
        console.print(context_table)

    if temp_dir:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
