import os, glob

for file in glob.glob('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we have duplicates
    times = content.count('    from app.utils.theme import theme_manager')
    if times > 1:
        print(f"Buscando duplicados en {file}...")
        
        # Un enfoque más robusto: reemplazar la inyección completa duplicada
        injection = """    from app.utils.theme import theme_manager
    BG = theme_manager.get_color("bg_color")
    SURFACE = theme_manager.get_color("surface")
    BORDER = theme_manager.get_color("border")
    PRIMARY = theme_manager.get_color("primary")
    REVENUE = theme_manager.get_color("revenue")
    EXPENSE = theme_manager.get_color("expense")
    TEXT = theme_manager.get_color("text_primary")
    DIM = theme_manager.get_color("text_secondary")
    FIELD_BG = theme_manager.get_color("field_bg")"""

        # En caso de que se haya inyectado más de una vez (porque la regex falló o match > 1)
        # Cortamos por `injection`
        parts = content.split(injection)
        # Conservar solo la última vez que aparece, o la primera. Mejor la primera.
        if len(parts) > 2: # means it appeared more than once
            print(f"Corrigiendo {file}")
            # Volvemos a unir
            new_content = parts[0] + injection
            # El resto simplemente lo pegamos sin la inyección
            for i in range(1, len(parts)):
                if parts[i].strip() == '': continue # Evitar dobles espacios
                new_content += parts[i]
            
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
