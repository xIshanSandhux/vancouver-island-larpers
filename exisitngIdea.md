**Penny is a personal finance and financial literacy app for Canadian students and young adults.** Its main purpose is to help someone answer: “What can I safely spend, where is my money going, and how can I build better habits?”

Your working demo is available at **[localhost:3000](http://localhost:3000)**.

Based on the screens, backend routes, and project decisions, here is what the project includes.

| Feature               | What users can do                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Home**              | See safe-to-spend money, how long it needs to last, account balances, monthly spending, upcoming bills, recent transactions, and an entry point to Penny AI. |
| **Accounts**          | View chequing, savings, and credit accounts; add or rename accounts; open account details with transactions and credit-limit usage.                          |
| **Transactions**      | Add, edit, delete, split, and search transactions. Filter by category, money in/out, and date. Import transaction history from CSV and export transactions.  |
| **Budgets**           | Create and edit category budgets, track remaining amounts, see overspending warnings, and copy budgets between months.                                       |
| **Recurring bills**   | Manage recurring expenses, view payment history, and mark bills paid. Marking a bill paid records the user’s statement—it does not send a payment.           |
| **Savings goals**     | Set a target amount and date, record contributions, track progress, and see the monthly savings needed.                                                      |
| **Spending insights** | Explore category breakdowns, needs versus wants, trends, and comparisons with previous periods.                                                              |
| **Penny AI**          | Ask questions about spending, affordability, budgets, savings goals, and payment scenarios using the app’s financial data.                                   |
| **Learn**             | Complete financial lessons and quizzes, earn XP and stars, build streaks, collect badges, and unlock difficulty levels.                                      |
| **Invest education**  | Learn investing foundations and Canadian account concepts, and explore illustrative compounding and fee scenarios.                                           |
| **Settings**          | Manage pay schedules, categories, accounts, imports, appearance, email reminder settings, and security information.                                          |

**The central feature is “Safe to spend.”**

Penny calculates spendable cash after reserving bills due before payday. When a budget exists, the result is also capped by the budget remaining. It never goes below zero.

It then shows how many days that amount needs to cover and a daily amount, with an on-track, tight, or empty status. These figures come from Python calculations.

**New users get a guided setup.**

The onboarding flow collects account balances, income or pay frequency, fixed bills, typical everyday spending, and a savings preference. Penny builds a proposed starting budget that:

- Reserves fixed bill costs.
- Allocates savings within the available income.
- Reduces flexible categories proportionally if the requested spending does not fit.
- Leaves unallocated money as a buffer.

The user reviews the plan before selecting **“Use this plan.”**

**Penny AI explains verified financial results.**

Example questions include:

- “Can I afford a $150 purchase before payday?”
- “What would happen if I reduced dining spending?”
- “How much should I save each month for my laptop?”
- “What changes if I pay more toward my credit card?”

The backend supplies account information and deterministic financial tools. The model can explain their results and prepare budget or goal proposals. **Those proposals require explicit approval before anything changes.** Replies also undergo checks that monetary figures and percentages match verified data or user-provided amounts.

Without a model API key, the coach returns built-in explanations.

**The learning system is more than a collection of articles.**

It covers budgeting, saving, tax, credit, rules and rights, and investing. It includes easy, medium, and hard levels, several question formats, hearts, stars, XP, badges, and streaks. Answers are graded on the server.

**The interface supports both web and an optional iPhone app.**

The project includes responsive layouts, mobile navigation, account detail pages, back transitions, loading skeletons, light and dark themes, appearance styles including Graphite, and an eye button that hides monetary amounts on the device. The iPhone shell uses Capacitor and shares the web interface.

**How the project works technically**

```text
Next.js frontend
      ↓
FastAPI backend
      ├── Financial calculations
      ├── Learning and quiz rules
      ├── Penny AI tools and approval checks
      └── In-memory storage or Supabase Postgres

Supabase Auth → sign-in when configured
```

The frontend uses TypeScript, React, Tailwind, and shadcn/ui components. The backend uses Python, FastAPI, and Pydantic. Money is represented as integer cents, with authoritative calculations performed in the backend.

**What is running right now**

Your current session uses fictional demo data and in-memory storage. The frontend and backend health checks passed, and the homepage and authenticated dashboard API returned HTTP 200. Data changes reset when the backend restarts.

Supabase sign-in, persistent storage, model-generated AI replies, and SMTP email delivery require their respective configuration. I have reviewed their implementation, but have not completed an end-to-end check of every feature.

Penny’s scope is an educational budgeting demo: it does not connect to banks, transfer money, execute investments, or retrieve real credit scores.

**A presentation-ready description:**

> Penny helps Canadian students understand their money through safe-to-spend guidance, expense tracking, budgets, savings goals, interactive lessons, and an AI coach grounded in verified calculations. Users stay in control by reviewing and approving AI-proposed changes.
