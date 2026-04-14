"""Translation pipeline - orchestrates TypeScript to Python conversion."""
from __future__ import annotations

from pathlib import Path

from tt.codegen import CodeGenerator
from tt.parser import parse_file


def run_translation(repo_root: Path, output_dir: Path) -> None:
    """Run the complete translation pipeline.
    
    Args:
        repo_root: Root of the repository (contains projects/)
        output_dir: Output directory for translated Python code
    """
    # Find the ROAI TypeScript file
    ts_path = repo_root / 'projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts'
    
    # Try fallback if not found (parent directory case)
    if not ts_path.exists():
        ts_path = repo_root.parent / 'projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts'
    
    if not ts_path.exists():
        raise FileNotFoundError(f"Could not find ROAI TypeScript file at {ts_path}")
    
    print(f"Parsing {ts_path}")
    
    # Parse the TypeScript file
    root_node = parse_file(ts_path)
    
    # Generate Python code
    generator = CodeGenerator()
    generated_code = generator.generate(root_node)
    
    # Collect imports from context
    imports = list(generator.ctx.imports_needed)
    
    # Add standard imports
    standard_imports = [
        "from decimal import Decimal",
        "from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator",
    ]
    
    # Combine all imports
    all_imports = standard_imports + imports
    import_block = "\n".join(sorted(set(all_imports)))
    
    # Assemble final output
    final_code = f'''{import_block}


{generated_code}
'''
    
    # Create output directory structure
    output_file = output_dir / 'app/implementation/portfolio/calculator/roai/portfolio_calculator.py'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    print(f"Writing to {output_file}")
    output_file.write_text(final_code)
    
    print(f"Translation complete: {output_file}")
