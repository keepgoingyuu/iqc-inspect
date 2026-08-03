import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import { router } from './router'
import { client } from './client/client.gen'

// 走相對路徑:開發時由 Vite proxy 轉發,正式部署與後端同源;cookie 隨請求帶上
client.setConfig({ baseUrl: '', credentials: 'include' })

createApp(App).use(ElementPlus).use(router).mount('#app')
