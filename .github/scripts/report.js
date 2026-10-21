// 주간/월간 진행 리포트: GitHub 데이터를 모아 이슈(Markdown)와 노션 페이지로 만든다.
// .github/workflows/progress-report.yml 에서 actions/github-script 로 불러 쓴다.

const DAY = 86400000;
const ymd = d => d.toISOString().slice(0, 10);

// 실행 시점 기준 직전 기간. weekly: 지난 월~일, monthly: 지난달 1일~말일
function periodFor(kind, now = new Date()) {
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  if (kind === 'monthly') {
    const start = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() - 1, 1));
    const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 0));
    const label = `${start.getUTCFullYear()}년 ${start.getUTCMonth() + 1}월`;
    return { kind, since: ymd(start), until: ymd(end), title: `📅 월간 리포트 ${label}` };
  }
  const daysSinceMonday = (today.getUTCDay() + 6) % 7;
  const thisMonday = new Date(today - daysSinceMonday * DAY);
  const start = new Date(thisMonday - 7 * DAY);
  const end = new Date(thisMonday - DAY);
  return { kind, since: ymd(start), until: ymd(end), title: `📊 주간 리포트 ${ymd(start)} ~ ${ymd(end)}` };
}

async function collect({ github, context, cfg, period }) {
  const repo = `${context.repo.owner}/${context.repo.repo}`;
  const range = `${period.since}..${period.until}`;
  const search = async q =>
    github.paginate(github.rest.search.issuesAndPullRequests, { q: `repo:${repo} ${q}`, per_page: 100 });

  const merged = await search(`is:pr is:merged merged:${range}`);
  const closedIssues = await search(`is:issue is:closed reason:completed closed:${range} -label:report:weekly -label:report:monthly`);
  const inProgress = await search('is:issue is:open label:status:in-progress');
  const blocked = await search('is:issue is:open label:status:blocked');
  const openPrs = await search('is:pr is:open');

  const releases = (await github.paginate(github.rest.repos.listReleases, { ...context.repo, per_page: 100 }))
    .filter(r => r.published_at && r.published_at.slice(0, 10) >= period.since && r.published_at.slice(0, 10) <= period.until)
    .map(r => ({ tag: r.tag_name, url: r.html_url }));

  const teamLabels = cfg.teams.map(t => t.label);
  const groups = cfg.teams.map(t => ({ id: t.id, name: t.name, label: t.label }));
  groups.push({ id: 'shared', name: '공용 / 팀 미지정', label: null });
  const pick = (items, label) =>
    items.filter(i => {
      const names = i.labels.map(l => l.name);
      return label ? names.includes(label) : !names.some(n => teamLabels.includes(n));
    });
  const teams = groups.map(g => ({
    ...g,
    merged: pick(merged, g.label),
    closedIssues: pick(closedIssues, g.label),
    inProgress: pick(inProgress, g.label),
    blocked: pick(blocked, g.label),
    openPrs: pick(openPrs, g.label),
  }));

  // 팀원별 기여: 병합된 PR 작성자, 완료된 이슈 담당자
  const people = new Map();
  const bump = (login, key) => {
    const p = people.get(login) || { login, prs: 0, issues: 0 };
    p[key] += 1;
    people.set(login, p);
  };
  merged.forEach(pr => bump(pr.user.login, 'prs'));
  closedIssues.forEach(i => (i.assignees || []).forEach(a => bump(a.login, 'issues')));
  const contributors = [...people.values()].sort((a, b) => b.prs + b.issues - (a.prs + a.issues));

  // AI 도구 활용: 병합된 PR 의 ai:* 라벨 (PR 자동화가 템플릿 체크/커밋 트레일러로 부여)
  const ai = Object.fromEntries(AI_TOOLS.map(([k]) => [k, 0]));
  let aiPrs = 0;
  for (const pr of merged) {
    const used = pr.labels.map(l => l.name).filter(n => n.startsWith('ai:')).map(n => n.slice(3));
    if (used.length) aiPrs += 1;
    used.forEach(k => { if (k in ai) ai[k] += 1; });
  }

  return {
    period,
    teams,
    contributors,
    ai,
    releases,
    totals: {
      merged: merged.length,
      closedIssues: closedIssues.length,
      inProgress: inProgress.length,
      blocked: blocked.length,
      people: contributors.length,
      aiPrs,
    },
  };
}

const AI_TOOLS = [
  ['claude', 'Claude Code'],
  ['codex', 'Codex'],
  ['grok', 'Grok'],
  ['other', '기타'],
];
const aiSummary = data =>
  `병합 PR ${data.totals.merged}개 중 ${data.totals.aiPrs}개 AI 활용 - ` +
  AI_TOOLS.map(([k, name]) => `${name} ${data.ai[k]}`).join(' · ');

const who = i => (i.assignees && i.assignees.length ? i.assignees : [i.user]).map(u => u.login).join(', ');
const SECTIONS = [
  ['merged', '✅ 병합된 PR'],
  ['closedIssues', '🏁 완료된 이슈'],
  ['inProgress', '🚧 진행 중 이슈'],
  ['blocked', '⛔ 막힌 이슈'],
  ['openPrs', '👀 열린 PR'],
];

function toMarkdown(data) {
  const { period, teams, contributors, releases } = data;
  let md = `## ${period.title}\n\n기간: ${period.since} ~ ${period.until}\n\n`;
  md += '| 팀 | 병합 PR | 완료 이슈 | 진행 중 | 막힘 | 열린 PR |\n|---|---|---|---|---|---|\n';
  for (const t of teams) {
    md += `| ${t.name} | ${t.merged.length} | ${t.closedIssues.length} | ${t.inProgress.length} | ${t.blocked.length} | ${t.openPrs.length} |\n`;
  }
  for (const t of teams) {
    const body = SECTIONS.filter(([k]) => t[k].length)
      .map(([k, title]) => `**${title}**\n${t[k].map(i => `- [#${i.number}](${i.html_url}) ${i.title} - \`${who(i)}\``).join('\n')}\n\n`)
      .join('');
    if (body) md += `\n### ${t.name}\n${body}`;
  }
  if (contributors.length) {
    md += `\n### 👥 팀원별 기여\n${contributors.map(p => `- \`${p.login}\`: 병합 PR ${p.prs}, 완료 이슈 ${p.issues}`).join('\n')}\n`;
  }
  if (data.totals.merged) {
    md += `\n### 🤖 AI 도구 활용\n- ${aiSummary(data)}\n`;
  }
  if (releases.length) {
    md += `\n### 🏷️ 릴리스\n${releases.map(r => `- [${r.tag}](${r.url})`).join('\n')}\n`;
  }
  md += '\n---\n_자동 생성 (.github/workflows/progress-report.yml). 막힌 작업은 회의에서 먼저 다뤄 주세요._';
  return md;
}

// ── 노션 ─────────────────────────────────────────────────────

const text = (content, link) => ({ type: 'text', text: { content: String(content).slice(0, 1900), link: link ? { url: link } : null } });
const block = (type, rich) => ({ object: 'block', type, [type]: { rich_text: rich } });

function toNotionBlocks(data) {
  const blocks = [block('heading_2', [text('팀별 요약')])];
  for (const t of data.teams) {
    blocks.push(
      block('bulleted_list_item', [
        text(`${t.name}: 병합 PR ${t.merged.length} · 완료 이슈 ${t.closedIssues.length} · 진행 중 ${t.inProgress.length} · 막힘 ${t.blocked.length} · 열린 PR ${t.openPrs.length}`),
      ]),
    );
  }
  for (const t of data.teams) {
    const sections = SECTIONS.filter(([k]) => t[k].length);
    if (!sections.length) continue;
    blocks.push(block('heading_2', [text(t.name)]));
    for (const [k, title] of sections) {
      blocks.push(block('heading_3', [text(title)]));
      for (const i of t[k]) {
        blocks.push(block('bulleted_list_item', [text(`#${i.number} ${i.title}`, i.html_url), text(` - ${who(i)}`)]));
      }
    }
  }
  if (data.contributors.length) {
    blocks.push(block('heading_2', [text('팀원별 기여')]));
    for (const p of data.contributors) {
      blocks.push(block('bulleted_list_item', [text(`${p.login}: 병합 PR ${p.prs}, 완료 이슈 ${p.issues}`)]));
    }
  }
  if (data.totals.merged) {
    blocks.push(block('heading_2', [text('AI 도구 활용')]));
    blocks.push(block('bulleted_list_item', [text(aiSummary(data))]));
  }
  if (data.releases.length) {
    blocks.push(block('heading_2', [text('릴리스')]));
    for (const r of data.releases) blocks.push(block('bulleted_list_item', [text(r.tag, r.url)]));
  }
  return blocks;
}

async function notion(path, method, token, body) {
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(`Notion API ${res.status}: ${json.message || JSON.stringify(json)}`);
  return json;
}

async function toNotion({ data, token, databaseId, reportUrl }) {
  const { period, totals, releases } = data;
  const properties = {
    제목: { title: [text(period.title)] },
    유형: { select: { name: period.kind === 'monthly' ? '월간' : '주간' } },
    기간: { date: { start: period.since, end: period.until } },
    '병합 PR': { number: totals.merged },
    '완료 이슈': { number: totals.closedIssues },
    '진행 중': { number: totals.inProgress },
    막힘: { number: totals.blocked },
    '참여 인원': { number: totals.people },
    'AI 활용 PR': { number: totals.aiPrs },
    릴리스: { rich_text: [text(releases.map(r => r.tag).join(', ') || '-')] },
    'GitHub 리포트': { url: reportUrl || null },
  };
  const blocks = toNotionBlocks(data);
  // 노션 API 는 한 번에 블록 100개까지 → 나머지는 이어 붙인다
  const page = await notion('pages', 'POST', token, {
    parent: { database_id: databaseId },
    properties,
    children: blocks.slice(0, 100),
  });
  for (let i = 100; i < blocks.length; i += 100) {
    await notion(`blocks/${page.id}/children`, 'PATCH', token, { children: blocks.slice(i, i + 100) });
  }
  return page.url;
}

module.exports = { periodFor, collect, toMarkdown, toNotionBlocks, toNotion };
