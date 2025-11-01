export function setByPath(obj: any, path: string, value: any) {
  // Преобразуем `a[0].b` → `a.0.b`
  const parts = path.replace(/\[(\d+)\]/g, ".$1").split(".");
  let cur = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i];
    if (cur[key] == null) {
      // создаём объект или массив в зависимости от следующего ключа
      const nextKey = parts[i + 1];
      cur[key] = /^\d+$/.test(nextKey) ? [] : {};
    }
    cur = cur[key];
  }

  cur[parts[parts.length - 1]] = value;
}

// lib/templates.ts
const RE = /\{\{\s*([A-Z0-9_\.]+)\s*\}\}/g;

type Vars = Record<string, string | number | boolean | null | undefined>;

export function expandTemplates<T>(input: T, vars: Vars): T {
  if (input == null) return input;
  if (Array.isArray(input)) {
    return input.map((v) => expandTemplates(v, vars)) as any;
  }
  if (typeof input === "object") {
    const out: any = Array.isArray(input) ? [] : {};
    for (const [k, v] of Object.entries(input as any)) {
      out[k] = expandTemplates(v, vars);
    }
    return out;
  }
  if (typeof input === "string") {
    return input.replace(RE, (_, key: string) => {
      const val = getVar(vars, key);
      return val == null ? "" : String(val);
    }) as any;
  }
  return input;
}

// Поддержка вложенных переменных: {{SITE.URL}} → vars["SITE.URL"] или vars.SITE.URL
function getVar(vars: Vars, key: string): any {
  if (key in vars) return (vars as any)[key];
  // доступ по точке
  const parts = key.split(".");
  let cur: any = vars;
  for (const p of parts) {
    if (cur && typeof cur === "object" && p in cur) cur = cur[p];
    else return undefined;
  }
  return cur;
}
