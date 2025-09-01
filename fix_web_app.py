#!/usr/bin/env python3
"""
Fix the indentation issue in web_app.py
"""

def fix_indentation():
    """Fix the indentation issue around line 692."""
    
    # Read the file with proper encoding
    with open('web_app.py', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Find and fix the problematic except block
    for i, line in enumerate(lines):
        if i >= 691 and i <= 696:  # Around the problematic area
            if 'except Exception as e:' in line:
                # Fix indentation to match try block (8 spaces)
                lines[i] = '        except Exception as e:\n'
            elif i > 691 and line.strip().startswith(('print(', 'import', 'return')):
                # Fix indentation for exception handler content (12 spaces)
                content = line.strip()
                lines[i] = f'            {content}\n'
    
    # Write back the fixed file
    with open('web_app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed indentation in web_app.py")

if __name__ == "__main__":
    fix_indentation()
