(async function () {
  const $q = document.getElementById("q");
  const $meta = document.getElementById("meta");
  const $results = document.getElementById("results");
  if (!$q || !$meta || !$results) return;

  // 轻量同义词/扩展词：你可以按自己站的主题继续补
  const SYN = {
    "低谷": ["低潮", "谷底", "困境", "逆境", "崩溃", "抑郁", "迷茫"],
    "独处": ["孤独", "独自", "一个人", "自处", "内向"],
    "家庭": ["亲情", "原生家庭", "父母", "家人", "婚姻", "关系"],
    "成长": ["成熟", "自我", "修复", "疗愈", "重建"],
    "爱情": ["亲密关系", "伴侣", "恋爱", "分手", "婚恋"],
    "意义": ["价值", "存在", "活着", "人生"],
  };

  function esc(s){
    return (s||"").replace(/[&<>"']/g, m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m]));
  }

  function normQuery(q){
    // 去掉多余空白（含全角空格），统一小写
    return (q || "")
      .replace(/\u3000/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function expandQuery(q){
    // 用同义词扩展：返回一个 query 列表（原词 + 扩展词）
    const raw = (q || "").trim();
    if (!raw) return [];
    const list = [raw];

    // 如果刚好命中 SYN key，则加入扩展
    if (SYN[raw]) list.push(...SYN[raw]);

    // 也支持：输入包含 key（例如“原生家庭”会触发“家庭”扩展）
    for (const k of Object.keys(SYN)) {
      if (raw !== k && raw.includes(k)) {
        list.push(...SYN[k]);
      }
    }

    // 去重
    return Array.from(new Set(list.map(s => s.trim()).filter(Boolean)));
  }

  // 拉取索引
  const res = await fetch("/seed.json", { cache: "no-store" });

  const data = await res.json();

  // 核心策略：标题/标签优先；content 几乎不参与（减少“误命中”）
  const fuse = new Fuse(data, {
    includeScore: true,
    ignoreLocation: true,
    // 中文 1 字也允许（否则“爱/家/书”搜不到）
    minMatchCharLength: 1,
    // 阈值略收紧，让结果更“准”
    threshold: 0.28,
    distance: 120,
    keys: [
      { name: "title",   weight: 0.62 },
      { name: "tags",    weight: 0.25 },
      { name: "author",  weight: 0.08 },
      { name: "summary", weight: 0.05 },
      // content 默认极低；如果你希望“全文检索感”强一点，把 0.01 调到 0.03
      { name: "content", weight: 0.01 }
    ]
  });

  function rankBoost(results, query){
    const q = query.trim();
    const lower = q.toLowerCase();

    return results
      .map(r => {
        const it = r.item;
        const t = (it.title || "");
        const tl = t.toLowerCase();
        let boost = 0;

        // 标题强优先
        if (tl === lower) boost -= 2.5;          // 完全命中
        else if (tl.startsWith(lower)) boost -= 1.0; // 前缀命中
        else if (tl.includes(lower)) boost -= 0.6;   // 包含命中

        // 标签次优先
        const tagsText = (it.tags || []).join(" ").toLowerCase();
        if (tagsText === lower) boost -= 0.8;
        else if (tagsText.includes(lower)) boost -= 0.35;

        // 作者弱优先（如果用户搜作者名）
        const al = (it.author || "").toLowerCase();
        if (al && (al === lower || al.includes(lower))) boost -= 0.25;

        // 书单略微优先（你也可以去掉这条）
        if (it.section === "lists") boost -= 0.25;

        return { item: it, score: (r.score ?? 1) + boost };
      })
      .sort((a,b)=>a.score - b.score)
      .map(x=>x.item);
  }

  function render(items, query){
    if (!query) { $results.innerHTML = ""; $meta.textContent = ""; return; }

    // 显示数量（最多 30）
    const show = items.slice(0, 30);
   $meta.textContent = `显示 ${show.length} / 共 ${items.length} 条结果`;

    if (!show.length) {
      $results.innerHTML = `<div style="padding:14px 0;color:rgba(0,0,0,.55);">没有找到结果</div>`;
      return;
    }

    $results.innerHTML = show.map(it => {
      const badge = it.section === "books" ? "书籍" : "书单";
      const sub = it.author ? `作者：${esc(it.author)} · ` : "";
      const tags = (it.tags || []).slice(0,4).map(t=>`<span style="display:inline-block;padding:2px 8px;border:1px solid rgba(0,0,0,.12);border-radius:999px;margin-right:6px;font-size:12px;color:rgba(0,0,0,.7);">${esc(t)}</span>`).join("");
      return `
        <a href="${it.url}" style="display:block;text-decoration:none;color:inherit;padding:14px 12px;border:1px solid rgba(0,0,0,.10);border-radius:14px;margin:10px 0;">
          <div style="font-size:12px;color:rgba(0,0,0,.55);margin-bottom:4px;">${badge}</div>
          <div style="font-size:16px;font-weight:650;line-height:1.35;margin-bottom:6px;">${esc(it.title)}</div>
          <div style="font-size:13px;color:rgba(0,0,0,.62);line-height:1.6;margin-bottom:8px;">${esc(it.summary || "")}</div>
          <div style="font-size:12px;color:rgba(0,0,0,.55);margin-bottom:8px;">${sub}${esc(it.date || "")}</div>
          <div>${tags}</div>
        </a>
      `;
    }).join("");
  }

  function searchNow(){
    const q0 = $q.value;
    const q = normQuery(q0);
    if (!q) return render([], "");

    // 同义词扩展 + 合并去重（按 URL 去重更稳）
    const queries = expandQuery(q);
    let merged = [];
    for (const qq of queries) merged = merged.concat(fuse.search(qq));

    // 以 url 去重（Fuse 返回的 item 引用可能重复）
    const seen = new Set();
    const dedup = [];
    for (const r of merged) {
      const u = r?.item?.url || "";
      if (!u || seen.has(u)) continue;
      seen.add(u);
      dedup.push(r);
    }

    const items = rankBoost(dedup, q);
    render(items, q);
  }

  // 输入节流
  $q.addEventListener("input", () => {
    clearTimeout($q._t);
    $q._t = setTimeout(searchNow, 120);
  });

  // 首次若 input 已有值（例如 /search/?q=xxx 回填），立刻跑一次
  if ($q.value && $q.value.trim()) searchNow();
})();
