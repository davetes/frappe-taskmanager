<template>
  <main class="page">
    <header class="hero">
      <div class="eyebrow">Task Manager</div>
      <h1>Keep the small things moving.</h1>
      <p class="lede">Add tasks, mark them done, and clear the clutter.</p>
    </header>

    <section class="panel">
      <form class="task-form" @submit.prevent="addTask">
        <input
          v-model.trim="newTask"
          class="task-input"
          type="text"
          placeholder="Add a new task"
          aria-label="Add a new task"
          :disabled="isSyncing"
        />
        <button class="task-button" type="submit" :disabled="!newTask || isSyncing">
          Add
        </button>
      </form>

      <div class="meta">
        <span>{{ remaining }} remaining</span>
        <div class="filters">
          <button
            v-for="option in filters"
            :key="option.value"
            class="filter"
            type="button"
            :class="{ active: filter === option.value }"
            @click="filter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <button
          class="clear"
          type="button"
          @click="clearCompleted"
          :disabled="!hasCompleted || isSyncing"
        >
          Clear completed
        </button>
      </div>

      <div class="status" v-if="error">
        {{ error }}
      </div>

      <div class="status" v-else-if="isLoading">
        Loading tasks...
      </div>

      <ul class="task-list" v-else-if="filteredTasks.length">
        <li v-for="task in filteredTasks" :key="task.id" class="task-item">
          <div class="task-row">
            <input
              class="task-check"
              type="checkbox"
              :checked="task.done"
              @change="toggleTask(task, $event)"
              :disabled="isSyncing"
            />
            <div class="task-content">
              <template v-if="editingId === task.id">
                <input
                  v-model.trim="editTitle"
                  class="task-edit"
                  type="text"
                  aria-label="Edit task"
                  :disabled="isSyncing"
                />
                <div class="task-actions">
                  <button class="task-action" type="button" @click="saveEdit(task)">
                    Save
                  </button>
                  <button class="task-action ghost" type="button" @click="cancelEdit">
                    Cancel
                  </button>
                </div>
              </template>
              <template v-else>
                <span class="task-title" :class="{ done: task.done }">
                  {{ task.title }}
                </span>
              </template>
            </div>
          </div>
          <div class="task-ops" v-if="editingId !== task.id">
            <button class="task-action" type="button" @click="startEdit(task)">
              Edit
            </button>
            <button class="task-remove" type="button" @click="removeTask(task.id)">
              Delete
            </button>
          </div>
        </li>
      </ul>

      <div class="empty" v-else>
        No tasks yet. Add your first one above.
      </div>
    </section>
  </main>
</template>

<script>
import { frappeRequest } from 'frappe-ui'

export default {
  name: 'Home',
  data() {
    return {
      newTask: '',
      tasks: [],
      filter: 'all',
      editingId: null,
      editTitle: '',
      isLoading: true,
      isSyncing: false,
      error: '',
      filters: [
        { label: 'All', value: 'all' },
        { label: 'Active', value: 'active' },
        { label: 'Completed', value: 'completed' },
      ],
    }
  },
  computed: {
    remaining() {
      return this.tasks.filter((task) => !task.done).length
    },
    hasCompleted() {
      return this.tasks.some((task) => task.done)
    },
    filteredTasks() {
      if (this.filter === 'active') {
        return this.tasks.filter((task) => !task.done)
      }
      if (this.filter === 'completed') {
        return this.tasks.filter((task) => task.done)
      }
      return this.tasks
    },
  },
  mounted() {
    this.fetchTasks()
  },
  methods: {
    async fetchTasks() {
      this.isLoading = true
      this.error = ''
      try {
        this.tasks = await frappeRequest({
          url: 'todo_app.api.list_tasks',
        })
      } catch (error) {
        this.error = error?.messages?.[0] || error.message || 'Failed to load tasks.'
      } finally {
        this.isLoading = false
      }
    },
    async addTask() {
      if (!this.newTask || this.isSyncing) return
      this.isSyncing = true
      this.error = ''
      try {
        const task = await frappeRequest({
          url: 'todo_app.api.add_task',
          params: { title: this.newTask },
        })
        this.tasks.unshift(task)
        this.newTask = ''
      } catch (error) {
        this.error = error?.messages?.[0] || error.message || 'Failed to add task.'
      } finally {
        this.isSyncing = false
      }
    },
    async toggleTask(task, event) {
      if (this.isSyncing) return
      const nextValue = event.target.checked
      const previous = task.done
      task.done = nextValue
      this.isSyncing = true
      this.error = ''
      try {
        const updated = await frappeRequest({
          url: 'todo_app.api.update_task',
          params: { task_id: task.id, done: nextValue },
        })
        task.done = updated.done
      } catch (error) {
        task.done = previous
        this.error = error?.messages?.[0] || error.message || 'Failed to update task.'
      } finally {
        this.isSyncing = false
      }
    },
    startEdit(task) {
      this.editingId = task.id
      this.editTitle = task.title
    },
    async saveEdit(task) {
      if (!this.editTitle || this.isSyncing) return
      this.isSyncing = true
      this.error = ''
      try {
        const updated = await frappeRequest({
          url: 'todo_app.api.update_task',
          params: { task_id: task.id, title: this.editTitle },
        })
        task.title = updated.title
        this.cancelEdit()
      } catch (error) {
        this.error = error?.messages?.[0] || error.message || 'Failed to update task.'
      } finally {
        this.isSyncing = false
      }
    },
    cancelEdit() {
      this.editingId = null
      this.editTitle = ''
    },
    async removeTask(id) {
      if (this.isSyncing) return
      this.isSyncing = true
      this.error = ''
      try {
        await frappeRequest({
          url: 'todo_app.api.delete_task',
          params: { task_id: id },
        })
        this.tasks = this.tasks.filter((task) => task.id !== id)
      } catch (error) {
        this.error = error?.messages?.[0] || error.message || 'Failed to delete task.'
      } finally {
        this.isSyncing = false
      }
    },
    async clearCompleted() {
      if (this.isSyncing || !this.hasCompleted) return
      const completed = this.tasks.filter((task) => task.done)
      if (!completed.length) return

      this.isSyncing = true
      this.error = ''
      try {
        await Promise.all(
          completed.map((task) =>
            frappeRequest({
              url: 'todo_app.api.delete_task',
              params: { task_id: task.id },
            })
          )
        )
        this.tasks = this.tasks.filter((task) => !task.done)
      } catch (error) {
        this.error = error?.messages?.[0] || error.message || 'Failed to clear tasks.'
      } finally {
        this.isSyncing = false
      }
    },
  },
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 64px 20px 96px;
  background: radial-gradient(circle at top, #f5f5f5 0%, #eef2f7 45%, #e3e8f0 100%);
  color: #101323;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.hero {
  max-width: 760px;
  margin: 0 auto 32px;
  text-align: center;
}

.eyebrow {
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.2em;
  color: #5d6475;
  margin-bottom: 12px;
}

.hero h1 {
  font-size: clamp(2rem, 3vw, 2.6rem);
  margin: 0 0 12px;
}

.lede {
  margin: 0;
  color: #4a5166;
  font-size: 1.05rem;
}

.panel {
  max-width: 760px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.1);
}

.task-form {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.task-input {
  flex: 1 1 260px;
  border: 1px solid #d9dee8;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 1rem;
  outline: none;
}

.task-input:focus {
  border-color: #6b7cff;
  box-shadow: 0 0 0 3px rgba(107, 124, 255, 0.2);
}

.task-button {
  border: none;
  border-radius: 12px;
  padding: 12px 18px;
  background: #1f2a44;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.task-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.meta {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  margin: 16px 2px 20px;
  color: #5d6475;
  font-size: 0.9rem;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.filter {
  border: 1px solid transparent;
  background: #f1f5fb;
  color: #4a5166;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.filter.active {
  border-color: #1f2a44;
  background: #e9edff;
  color: #1f2a44;
}


.clear {
  background: transparent;
  border: none;
  color: #e33e45;
  font-weight: 600;
  cursor: pointer;
}

.clear:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.task-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f6f8fb;
}

.task-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-weight: 500;
  flex: 1;
}

.task-check {
  width: 18px;
  height: 18px;
  accent-color: #2f6fed;
}

.task-content {
  flex: 1;
  display: grid;
  gap: 8px;
}

.task-edit {
  border: 1px solid #d9dee8;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 0.95rem;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.task-action {
  border: none;
  background: #1f2a44;
  color: #ffffff;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.task-action.ghost {
  background: #e2e8f0;
  color: #1f2a44;
}

.task-ops {
  display: flex;
  gap: 8px;
  align-items: center;
}

.task-title.done {
  text-decoration: line-through;
  color: #8b93a6;
}

.task-remove {
  border: none;
  background: #fff1f2;
  color: #b42318;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 28px 0 12px;
  color: #6b7280;
}

.status {
  text-align: center;
  padding: 18px 0;
  color: #6b7280;
}

@media (max-width: 640px) {
  .panel {
    padding: 20px;
  }

  .meta {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .task-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
