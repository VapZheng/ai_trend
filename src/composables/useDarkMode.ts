import { computed, onMounted, ref } from 'vue';

export function useDarkMode() {
  const isDarkMode = ref(false);

  // 检查系统偏好
  const prefersDark = computed(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // 初始化深色模式
  const initDarkMode = () => {
    // 检查本地存储
    const stored = localStorage.getItem('theme-mode');
    if (stored) {
      isDarkMode.value = stored === 'dark';
    } else {
      // 使用系统偏好
      isDarkMode.value = prefersDark.value;
    }
    applyDarkMode();
  };

  // 应用深色模式
  const applyDarkMode = () => {
    const html = document.documentElement;
    if (isDarkMode.value) {
      html.classList.add('dark-mode');
    } else {
      html.classList.remove('dark-mode');
    }
    localStorage.setItem('theme-mode', isDarkMode.value ? 'dark' : 'light');
  };

  // 切换深色模式
  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value;
    applyDarkMode();
  };

  // 设置深色模式
  const setDarkMode = (value: boolean) => {
    isDarkMode.value = value;
    applyDarkMode();
  };

  // 监听系统主题变化
  onMounted(() => {
    initDarkMode();

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme-mode')) {
        isDarkMode.value = e.matches;
        applyDarkMode();
      }
    };

    // 兼容不同浏览器
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      mediaQuery.addListener(handleChange);
    }
  });

  return {
    isDarkMode,
    toggleDarkMode,
    setDarkMode,
    prefersDark,
  };
}
