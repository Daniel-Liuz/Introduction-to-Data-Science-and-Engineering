import { test } from './fixture';

test('download esi data', async ({ page, ai, aiTap, aiInput, aiWaitFor,aiAction }) => {
  // 步骤 1: 导航到目标网站  
 // 步骤 1: 导航到目标网站
  await page.goto('https://esi.clarivate.com');
  await aiWaitFor('界面加载成功', { timeoutMs: 100000 });
  await aiInput('10235501456@stu.ecnu.edu.cn', 'Email address input');
  await aiInput('Liuziyang225678!', 'Password input');
  await aiTap('Sign In button');


  // 步骤 3: 智能等待登录成功并加载主界面
  // 等待直到 "Top Papers by Institutions" 标题出现，表明已进入主界面
  await aiWaitFor('界面中包含 "Top Papers by Research Fields"', { timeoutMs: 500000 });

  // 步骤 4: 确保结果列表设置为 "Institutions"
  // 这是一个保险步骤，通常默认就是这个选项
  await aiTap('点击Result lists下方的“Research Fields”选择框');
  await aiTap('选择“Institutions”选项');

  // 步骤 5: 获取单个CASE

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Agricultural Sciences的+号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institutions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Agricultural Sciences的"一"号'); 
  await aiTap('Biology 的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Biology的"一"号'); 
  await aiTap('Chemistry 的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });
 
  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Chemistry的"一"号'); 
  await aiTap('Clinical Medicine 的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Clinical Medicine的"一"号'); 
  await aiTap('Computer Science 的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Computer Science的"一"号'); 
  await aiTap('Economics & Business的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Economics & Business的"一"号'); 
  await aiTap('Engineering的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Engineering的"一"号'); 
  await aiTap('Environment的"+"号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Environment的"一"号'); 
  await aiAction('滚动到Geosciences的"+"号');
  await aiTap('Geosciences的"+"号'); 
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Geosciences的"一"号'); 
  await aiAction('滚动到Immunology的"+"号');
  await aiTap('Immunology的"+"号'); 
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Immunology的"一"号');
  await aiAction('滚动到Materials Science的"+"号');
  await aiTap('Materials Science的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Materials Science的"一"号'); 
  await aiAction('滚动到Mathematics的"+"号');
  await aiTap('Mathematics的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Mathematics的"一"号'); 
  await aiAction('滚动到Microbiology的"+"号');
  await aiTap('Microbiology的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Microbiology的"一"号'); 
  await aiAction('滚动到Molecular Biology & Genetics的"+"号');
  await aiTap('Molecular Biology & Genetics的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Molecular Biology & Genetics的"一"号'); 
  await aiAction('滚动到Multidisciplinary的"+"号');
  await aiTap('Multidisciplinary的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Multidisciplinary的"一"号'); 
  await aiAction('滚动到Neuroscience & Behavior的"+"号');
  await aiTap('Neuroscience & Behavior的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Neuroscience & Behavior的"一"号'); 
  await aiAction('滚动到Pharmacology & Toxicology的"+"号');
  await aiTap('Pharmacology & Toxicology的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Pharmacology & Toxicology的"一"号'); 
  await aiAction('滚动到Physics的"+"号');
  await aiTap('Physics的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Physics的"一"号'); 
  await aiAction('滚动到Plant & Animal Science的"+"号');
  await aiTap('Plant & Animal Science的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Plant & Animal Science的"一"号'); 
  await aiAction('滚动到Psychiatry/Psychology的"+"号');
  await aiTap('Psychiatry/Psychology的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Psychiatry/Psychology的"一"号'); 
  await aiAction('滚动到Social Sciences, General的"+"号');
  await aiTap('Social Sciences, General的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Social Sciences, General的"一"号'); 
  await aiAction('滚动到Space Science的"+"号');
  await aiTap('Space Science的"+"号');
  await aiAction('滚动到页面上方');
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institut ions"', { timeoutMs: 100000 });
});