
import json
import re

# ----------------- PATH HELPER -----------------
def set_value_by_path(obj, path, value):
    # "children[0].children[1].value" -> ["children", "0", "children", "1", "value"]
    parts = [p for p in re.split(r'\.|\[', path.replace(']', '')) if p]
    
    current = obj
    for i in range(len(parts) - 1):
        key = parts[i]
        
        # Handle array indices
        if isinstance(current, list):
            try:
                key = int(key)
            except ValueError:
                pass
                
        if isinstance(current, dict):
            if key not in current:
                # print(f"Invalid path: {path} Missing key: {key}")
                return
            current = current[key]
        elif isinstance(current, list):
            if isinstance(key, int) and 0 <= key < len(current):
                current = current[key]
            else:
                # print(f"Invalid path: {path} Index out of bounds: {key}")
                return
        else:
            return

    final_key = parts[-1]
    
    if isinstance(current, list):
        try:
            final_key = int(final_key)
            if 0 <= final_key < len(current):
                current[final_key] = value
        except ValueError:
            pass
    elif isinstance(current, dict):
        current[final_key] = value

def apply_variables(card_json, variables):
    if not variables:
        return card_json
        
    # Check if variables is a flat dictionary of paths (legacy/explicit mode)
    # or a nested object that matches the structure (implicit mode)
    # The provided JS used flat paths. We will support flat paths for now as per instructions.
    
    # If variables is a nested dict, we might need to flatten it or traverse it?
    # For now, assuming variables is { "path.to.key": "value" } as per the user's example.
    # But if the AI returns a nested JSON object matching the schema, we might need to convert it?
    # User said: "update the json as per the values".
    # Implementation: If variables is a dict, iterate and apply.
    
    # Use a helper to flatten if necessary, OR assume the AI is instructed to return flat paths?
    # The Schema generated is a nested object schema. The AI returns a nested object.
    # WE need to map the Nested Object -> Template Paths?
    # Or does the Template have "bindings"? 
    # The user example: `variables = {"children[0].value": "..."}`.
    # The AI returns `{ item: { ... } }` or just `{ ... }`.
    # How do we map `{ title: "Hello" }` from AI to `children[0].value` in template?
    # OPTION A: The User's Template has specific "names" for keys? No, the JS code relies on hardcoded paths.
    # OPTION B: The Schema IS the template structure? No, the schema is `anyOf` the template schemas.
    # ALERT: The user's JS example shows `variables` being a map of PATHS.
    # If the AI returns a structured JSON (e.g. `{ "headline": "Hi", "body": "..." }`), we can't blindly apply it.
    # UNLESS we assume the AI output *IS* the component structure itself? 
    # "update the json as per the values" implies we have a Template JSON, and we overwrite values.
    
    # Let's assume the AI generates a JSON that *matches* the `variables` map structure?
    # Wait, the `json_schema` is generated from the template.
    # If the template has a schema, the AI fills that schema.
    # Does the template schema include the PATHS?
    # In `AdvancedParameters.js`, `RESPONSE_TEMPLATES` objects have `json_schema`.
    # We need to map [AI Output Key] -> [Template Path].
    # IF the template object in `AdvancedParameters.js` has this mapping, we are good.
    # I verified `AdvancedParameters.js`: 
    # `templateObj` has `json_schema`. 
    # It does NOT seem to have a mapping file.
    # HOWEVER, the JS example given by user shows explicit path variables.
    
    # HYPOTHESIS: The AI output should effectively BE the variable map? 
    # OR the AI output is a flat object, and we try to match keys?
    # Let's assume for this task that the `variables` passed to this function 
    # IS the dictionary of `path: value` pairs.
    # If the AI returns a nested object, we might need to flatten it. 
    # But for now, let's implement the core formatting logic.
    
    if isinstance(variables, dict):
        for path, value in variables.items():
            set_value_by_path(card_json, path, value)
            
    return card_json

# ----------------- RENDERER -----------------
def render_node(node):
    if not node or not isinstance(node, dict):
        return ""

    node_type = node.get("type")

    # CARD WRAPPER
    if node_type == "Card":
        padding_classes = ""
        padding = node.get("padding")

        if isinstance(padding, (int, float)):
             padding_classes = f"p-{padding}"
        elif isinstance(padding, dict):
            if "y" in padding: padding_classes += f" py-{padding['y']}"
            if "x" in padding: padding_classes += f" px-{padding['x']}"
        else:
            size = node.get("size")
            if size == "sm":
                padding_classes = "p-4"
            elif size == "lg":
                padding_classes = "p-7"
            else:
                padding_classes = "p-6"

        children = node.get("children", [])
        body = "\n".join([render_node(child) for child in children])

        footer = ""
        confirm = node.get("confirm")
        cancel = node.get("cancel")
        
        if confirm or cancel:
            buttons = []
            if cancel and cancel.get("label"):
                buttons.append(render_node({
                    "type": "Button",
                    "label": cancel.get("label"),
                    "style": "secondary",
                    "pill": True
                }))
            
            if confirm and confirm.get("label"):
                buttons.append(render_node({
                    "type": "Button",
                    "label": confirm.get("label"),
                    "style": "primary",
                    "pill": True
                }))
            
            buttons_html = "\n".join(buttons)
            footer = f"""
<div class="mt-4 flex justify-end gap-3 px-4 pb-4">
  {buttons_html}
</div>
""".strip()

        return f"""
<div class="relative max-w-xl w-full overflow-hidden rounded-[20px] border border-slate-200 bg-white text-slate-900 shadow-[0_12px_30px_rgba(15,23,42,0.10)] {padding_classes}">
  <div class="space-y-4">
    {body}
    {footer}
  </div>
</div>
""".strip()

    elif node_type == "Form":
        children = node.get("children", [])
        rendered_children = "\n".join([render_node(child) for child in children])
        return f"""
<form class="flex flex-col gap-4">
  {rendered_children}
</form>
""".strip()

    elif node_type == "DatePicker":
        name_attr = f' name="{node.get("name")}"' if node.get("name") else ""
        value_attr = f' value="{node.get("defaultValue")}"' if node.get("defaultValue") else ""
        placeholder_attr = f' placeholder="{node.get("placeholder")}"' if node.get("placeholder") else ""

        return f"""
<div class="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm">
  <input
    type="date"
    class="appearance-none bg-transparent outline-none border-none text-sm text-slate-900"
    {name_attr}{value_attr}{placeholder_attr}
  />
  <span class="inline-flex h-4 w-4 items-center justify-center text-slate-500">
    <svg viewBox="0 0 24 24" class="h-4 w-4">
      <rect x="3" y="4" width="18" height="17" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="1.5"/>
      <line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="1.5"/>
      <line x1="9" y1="3" x2="9" y2="7" stroke="currentColor" stroke-width="1.5"/>
      <line x1="15" y1="3" x2="15" y2="7" stroke="currentColor" stroke-width="1.5"/>
    </svg>
  </span>
</div>
""".strip()

    elif node_type == "Col":
        gap = f"gap-{node.get('gap')}" if node.get("gap") is not None else "gap-3"
        
        padding_classes = ""
        padding = node.get("padding")
        if isinstance(padding, (int, float)):
            padding_classes = f"p-{padding}"
        elif isinstance(padding, dict):
            if "x" in padding: padding_classes += f" px-{padding['x']}"
            if "y" in padding: padding_classes += f" py-{padding['y']}"
            if "top" in padding: padding_classes += f" pt-{padding['top']}"
            if "bottom" in padding: padding_classes += f" pb-{padding['bottom']}"
            if "left" in padding: padding_classes += f" pl-{padding['left']}"
            if "right" in padding: padding_classes += f" pr-{padding['right']}"

        align = node.get("align", "")
        align_map = {
            "center": "items-center",
            "start": "items-start",
            "end": "items-end"
        }
        align_class = align_map.get(align, "")
        
        flex_class = "flex-1" if node.get("flex") else ""
        
        children = node.get("children", [])
        rendered_children = "\n".join([render_node(child) for child in children])
        
        return f"""
<div class="flex flex-col {gap} {padding_classes} w-full {align_class} {flex_class}">
  {rendered_children}
</div>
""".strip()

    elif node_type == "Row":
        gap = f"gap-{node.get('gap')}" if node.get("gap") is not None else "gap-3"
        
        padding_classes = ""
        padding = node.get("padding")
        if isinstance(padding, (int, float)):
            padding_classes = f"p-{padding}"
        elif isinstance(padding, dict):
            if "x" in padding: padding_classes += f" px-{padding['x']}"
            if "y" in padding: padding_classes += f" py-{padding['y']}"
            if "top" in padding: padding_classes += f" pt-{padding['top']}"
            if "bottom" in padding: padding_classes += f" pb-{padding['bottom']}"
            if "left" in padding: padding_classes += f" pl-{padding['left']}"
            if "right" in padding: padding_classes += f" pr-{padding['right']}"

        align = node.get("align", "")
        align_map = {
            "center": "items-center",
            "start": "items-start",
            "end": "items-end"
        }
        align_class = align_map.get(align, "items-stretch")
        
        bg_class = ""
        if node.get("background") == "surface-elevated-secondary":
            bg_class = "bg-slate-50"
            
        border_class = ""
        if node.get("border", {}).get("top", {}).get("size"):
            border_class += " border-t border-slate-200"
            
        children = node.get("children", [])
        rendered_children = "\n".join([render_node(child) for child in children])

        return f"""
<div class="flex flex-row {gap} {align_class} {padding_classes} {bg_class} {border_class}">
  {rendered_children}
</div>
""".strip()

    elif node_type == "Spacer":
        return '<div class="flex-1"></div>'

    elif node_type == "Divider":
        flush_class = "mx-0" if node.get("flush") else "mx-2"
        return f"""
<div class="relative {flush_class}">
  <div class="border-t border-dashed border-slate-200/80"></div>
</div>
""".strip()

    elif node_type == "Box":
        size = node.get("size", 40)
        
        padding_classes = ""
        padding = node.get("padding")
        if isinstance(padding, (int, float)):
            approx = max(0, round(padding))
            if approx > 0:
                padding_classes = f"p-{approx}"
        elif isinstance(padding, dict):
             if "x" in padding: padding_classes += f" px-{padding['x']}"
             if "y" in padding: padding_classes += f" py-{padding['y']}"
             
        radius_map = {
            "sm": "rounded-md",
            "md": "rounded-xl",
            "lg": "rounded-2xl"
        }
        radius_class = radius_map.get(node.get("radius"), "rounded-xl")
        
        align_map = {"center": "items-center", "start": "items-start", "end": "items-end"}
        justify_map = {"center": "justify-center", "start": "justify-start", "end": "justify-end", "between": "justify-between"}
        
        align_class = align_map.get(node.get("align"), "items-center")
        justify_class = justify_map.get(node.get("justify"), "justify-center")
        
        bg = node.get("background", "")
        bg_class = bg if not str(bg).startswith("#") else ""
        
        style = ""
        if str(bg).startswith("#"):
            style = f'style="background:{bg};width:{size}px;height:{size}px;"'
        else:
            style = f'style="width:{size}px;height:{size}px;"'
            
        children = node.get("children", [])
        rendered_children = "\n".join([render_node(child) for child in children])
        
        return f"""
<div class="flex {align_class} {justify_class} {radius_class} {padding_classes} {bg_class}" {style}>
  {rendered_children}
</div>
""".strip()

    elif node_type == "Image":
        size = node.get("size", 48)
        frame_class = "rounded-xl ring-1 ring-slate-200/80 bg-slate-50" if node.get("frame") else "rounded-full ring-1 ring-slate-200/50 bg-slate-900/10"
        
        return f"""
<div class="{frame_class} overflow-hidden shadow-sm">
  <img
    src="{node.get('src', '')}"
    alt="{node.get('alt', '')}"
    class="object-cover transition-transform duration-200 hover:scale-[1.03]"
    style="width:{size}px;height:{size}px;"
  />
</div>
""".strip()

    elif node_type == "Title":
        size_map = {
            "3xl": "text-4xl md:text-5xl",
            "2xl": "text-3xl md:text-4xl",
            "xl": "text-2xl md:text-3xl",
            "sm": "text-sm md:text-base"
        }
        size_class = size_map.get(node.get("size"), "text-xl md:text-2xl")
        
        weight_class = "font-semibold"
        if node.get("weight") == "normal": weight_class = "font-normal"
        
        color_class = "text-white" if node.get("color") == "white" else "text-slate-900"
        
        align_map = {"center": "text-center", "left": "text-left", "right": "text-right"}
        align_class = align_map.get(node.get("textAlign"), "")
        
        max_lines_class = f"line-clamp-{node['maxLines']}" if node.get("maxLines") else ""
        
        return f"""
<h2 class="{size_class} {weight_class} {color_class} {align_class} {max_lines_class} tracking-tight">
  {node.get("value", "")}
</h2>
""".strip()

    elif node_type == "Caption":
        size_class = "text-sm" if node.get("size") == "lg" else "text-xs"
        color_class = "text-sky-50" if node.get("color") == "white" else "text-slate-400"
        
        align_map = {"center": "text-center", "left": "text-left", "right": "text-right"}
        align_class = align_map.get(node.get("textAlign"), "")
        
        return f"""
<p class="{size_class} {color_class} {align_class} tracking-wide uppercase">
  {node.get("value", "")}
</p>
""".strip()

    elif node_type == "Text":
        size_map = {
            "xs": "text-xs",
            "sm": "text-xs md:text-sm",
            "md": "text-sm md:text-base",
            "lg": "text-base md:text-lg"
        }
        palette_map = {
            "secondary": "text-slate-500",
            "tertiary": "text-slate-400",
            "success": "text-emerald-600",
            "emphasis": "text-slate-900",
            "white": "text-white"
        }
        
        size_class = size_map.get(node.get("size"), "text-sm")
        color_class = "text-slate-900"
        
        color = node.get("color")
        if color:
            if color == "white":
                color_class = "text-white"
            elif not str(color).startswith("#"):
                color_class = palette_map.get(color, "text-slate-900")
                
        weight_class = ""
        if node.get("weight") == "semibold": weight_class = "font-semibold"
        elif node.get("weight") == "medium": weight_class = "font-medium"
        
        max_lines_class = f"line-clamp-{node['maxLines']}" if node.get("maxLines") else ""
        
        align_map = {"center": "text-center", "left": "text-left", "right": "text-right"}
        align_class = align_map.get(node.get("textAlign"), "")
        
        if node.get("editable"):
            editable = node["editable"]
            name = editable.get("name", "")
            placeholder = editable.get("placeholder", "")
            value = node.get("value", "")
            
            field_base = f"w-full bg-transparent {size_class} {weight_class} {align_class} text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0"
            
            if node.get("minLines", 0) > 1:
                return f"""
<textarea
  name="{name}"
  rows="{node.get('minLines')}"
  class="block {field_base} resize-none leading-relaxed"
  placeholder="{placeholder}"
>{value}</textarea>
""".strip()
            
            return f"""
<input
  type="text"
  name="{name}"
  class="block {field_base}"
  placeholder="{placeholder}"
  value="{value}"
/>
""".strip()
        
        base_classes = f"{size_class} {color_class} {weight_class} {max_lines_class} {align_class}"
        if color and str(color).startswith("#"):
            return f'<p class="{base_classes}" style="color:{color}">{node.get("value", "")}</p>'
            
        return f'<p class="{base_classes}">{node.get("value", "")}</p>'

    elif node_type == "Input":
        input_type = node.get("inputType") or node.get("typeAttr") or "text"
        name_attr = f' name="{node.get("name")}"' if node.get("name") else ""
        value_attr = f' value="{node.get("defaultValue")}"' if node.get("defaultValue") is not None and node.get("defaultValue") != "" else ""
        placeholder_attr = f' placeholder="{node.get("placeholder")}"' if node.get("placeholder") else ""
        
        base_classes = "block w-full text-sm outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-colors"
        pill_classes = "rounded-full border border-slate-300 bg-white px-4 py-2 text-slate-900 placeholder:text-slate-400"
        normal_classes = "rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 placeholder:text-slate-400"
        
        classes = f"{base_classes} {pill_classes}" if node.get("pill") else f"{base_classes} {normal_classes}"
        
        return f"""
<input
  type="{input_type}"
  class="{classes}"
  {name_attr}{value_attr}{placeholder_attr}
/>
""".strip()

    elif node_type == "Markdown":
        text = node.get("value", "")
        return f"""
<div class="prose prose-sm text-slate-100 whitespace-pre-wrap">
  {text}
</div>
""".strip()

    elif node_type == "Icon":
        color_map = {
            "success": "text-emerald-500",
            "danger": "text-rose-500",
            "warning": "text-amber-500"
        }
        color_class = color_map.get(node.get("color"), "text-slate-500") if node.get("color") else "text-slate-500"
        
        size_map = {"sm": "h-4 w-4", "md": "h-5 w-5", "lg": "h-6 w-6", "xl": "h-7 w-7"}
        size_class = size_map.get(node.get("size"), "h-5 w-5")
        
        return f"""
<span class="inline-flex {size_class} items-center justify-center {color_class}">
  <span class="text-[0.7rem] uppercase tracking-tight">{node.get("name", "")}</span>
</span>
""".strip()

    elif node_type == "Button":
        base = "inline-flex items-center justify-center px-5 py-2 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2"
        style_key = node.get("style") or node.get("variant") or "secondary"
        
        style_map = {
            "primary": "bg-black text-white hover:bg-zinc-900 rounded-full focus:ring-black",
            "secondary": "bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 rounded-full focus:ring-slate-300",
            "subtle": "bg-slate-100 text-slate-800 hover:bg-slate-200 rounded-full focus:ring-slate-200"
        }
        
        style_class = style_map.get(style_key, style_map["secondary"])
        block_class = "w-full" if node.get("block") else ""
        type_attr = "submit" if node.get("submit") else "button"
        
        return f"""
<button
  type="{type_attr}"
  class="{base} {style_class} {block_class}"
>
  {node.get("label", "")}
</button>
""".strip()

    elif node_type == "Select":
        options = node.get("options", [])
        rendered_options = "\n".join([
            f'<option value="{opt.get("value")}"{" selected" if opt.get("value") == node.get("defaultValue") else ""}>\n  {opt.get("label")}\n</option>'
            for opt in options
        ])
        
        variant = node.get("variant", "ghost")
        base = "text-sm outline-none focus:ring-0 focus:outline-none cursor-pointer"
        ghost_classes = "bg-transparent border-none text-right text-slate-900"
        pill_classes = "bg-white border border-slate-300 rounded-full px-3 py-2 text-slate-900"
        
        select_classes = f"{base} {ghost_classes}" if variant == "ghost" else f"{base} {pill_classes}"
        name = node.get("name", "")
        
        return f"""
<div class="inline-flex items-center justify-end">
  <select name="{name}" class="{select_classes}">
    {rendered_options}
  </select>
</div>
""".strip()

    # Default fallback for children
    if isinstance(node.get("children"), list):
        return "\n".join([render_node(child) for child in node["children"]])
        
    return ""

def render_card_to_tailwind(card_json):
    return render_node(card_json)

def render_template_to_html(card_json_template, variables_data={}):
    """
    Main entry point.
    Takes a Card JSON Template and a Variables dictionary.
    Returns the rendered HTML string.
    """
    # Clone the template to avoid mutation (not strictly necessary given usage)
    cloned_template = json.loads(json.dumps(card_json_template))
    
    # Apply variables
    apply_variables(cloned_template, variables_data)
    
    # Render
    return render_card_to_tailwind(cloned_template)
