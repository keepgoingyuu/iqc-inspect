import { createApp } from 'vue'
import './index.css'
import 'vue-sonner/style.css'
import App from './App.vue'
import { router } from './router'
import { client } from './client/client.gen'

// 走相對路徑:開發時由 Vite proxy 轉發,正式部署與後端同源;cookie 隨請求帶上
client.setConfig({ baseUrl: '', credentials: 'include' })

// dark-first:預設深色,使用者切換後記住偏好
document.documentElement.classList.toggle('dark', localStorage.getItem('theme') !== 'light')

createApp(App).use(router).mount('#app')
