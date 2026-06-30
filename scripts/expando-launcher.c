#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define EXPANDO_PYTHON_VERSION "3.12"

typedef int (*py_bytes_main_fn)(int, char **);

static int copy_string(char *destination, size_t destination_size, const char *source) {
  size_t length = strlen(source);
  if (length + 1 > destination_size) {
    return -1;
  }
  memcpy(destination, source, length + 1);
  return 0;
}

static int join_path(char *destination, size_t destination_size, const char *left, const char *right) {
  int written = snprintf(destination, destination_size, "%s/%s", left, right);
  if (written < 0 || (size_t)written >= destination_size) {
    return -1;
  }
  return 0;
}

static int get_executable_path(char *destination, size_t destination_size) {
  char raw_path[PATH_MAX];
  uint32_t raw_size = sizeof(raw_path);
  if (_NSGetExecutablePath(raw_path, &raw_size) != 0) {
    fprintf(stderr, "Expando launcher path is too long.\n");
    return -1;
  }
  if (realpath(raw_path, destination) != NULL) {
    return 0;
  }
  return copy_string(destination, destination_size, raw_path);
}

static int derive_app_root(const char *executable_path, char *destination, size_t destination_size) {
  const char *marker = "/Contents/MacOS/";
  const char *marker_position = strstr(executable_path, marker);
  if (marker_position == NULL) {
    fprintf(stderr, "Expando must be launched from inside Expando.app.\n");
    return -1;
  }
  size_t length = (size_t)(marker_position - executable_path);
  if (length + 1 > destination_size) {
    fprintf(stderr, "Expando app path is too long.\n");
    return -1;
  }
  memcpy(destination, executable_path, length);
  destination[length] = '\0';
  return 0;
}

static int set_path_environment(const char *name, const char *first_path) {
  const char *current = getenv(name);
  if (current == NULL || current[0] == '\0') {
    return setenv(name, first_path, 1);
  }

  size_t needed = strlen(first_path) + strlen(current) + 2;
  char *combined = calloc(needed, sizeof(char));
  if (combined == NULL) {
    return -1;
  }
  snprintf(combined, needed, "%s:%s", first_path, current);
  int result = setenv(name, combined, 1);
  free(combined);
  return result;
}

static int python_runtime_from_home(
  const char *home,
  char *library_path,
  size_t library_path_size
) {
  if (join_path(library_path, library_path_size, home, "Python") != 0) {
    return -1;
  }
  return access(library_path, R_OK) == 0 ? 0 : -1;
}

static int find_python_runtime(
  const char *app_root,
  char *python_home,
  size_t python_home_size,
  char *library_path,
  size_t library_path_size
) {
  char embedded_home[PATH_MAX];
  int written = snprintf(
    embedded_home,
    sizeof(embedded_home),
    "%s/Contents/Frameworks/Python.framework/Versions/%s",
    app_root,
    EXPANDO_PYTHON_VERSION
  );
  if (written >= 0 && (size_t)written < sizeof(embedded_home)) {
    if (python_runtime_from_home(embedded_home, library_path, library_path_size) == 0) {
      return copy_string(python_home, python_home_size, embedded_home);
    }
  }

  fprintf(stderr, "Expando is missing its embedded Python %s runtime. Reinstall Expando.\n", EXPANDO_PYTHON_VERSION);
  return -1;
}

int main(int argc, char **argv) {
  char executable_path[PATH_MAX];
  char app_root[PATH_MAX];
  char resources_path[PATH_MAX];
  char site_packages_path[PATH_MAX];
  char python_home[PATH_MAX];
  char python_library[PATH_MAX];

  if (get_executable_path(executable_path, sizeof(executable_path)) != 0) {
    return 1;
  }
  if (derive_app_root(executable_path, app_root, sizeof(app_root)) != 0) {
    return 1;
  }
  if (join_path(resources_path, sizeof(resources_path), app_root, "Contents/Resources") != 0) {
    fprintf(stderr, "Expando resources path is too long.\n");
    return 1;
  }
  if (join_path(site_packages_path, sizeof(site_packages_path), resources_path, "site-packages") != 0) {
    fprintf(stderr, "Expando Python path is too long.\n");
    return 1;
  }
  if (
    find_python_runtime(
      app_root,
      python_home,
      sizeof(python_home),
      python_library,
      sizeof(python_library)
    ) != 0
  ) {
    return 1;
  }

  setenv("EXPANDO_RESOURCES", resources_path, 1);
  setenv("PYTHONDONTWRITEBYTECODE", "1", 1);
  setenv("PYTHONNOUSERSITE", "1", 1);
  setenv("PYTHONHOME", python_home, 1);
  setenv("PYTHONEXECUTABLE", executable_path, 1);
  set_path_environment("PYTHONPATH", site_packages_path);

  void *python = dlopen(python_library, RTLD_NOW | RTLD_GLOBAL);
  if (python == NULL) {
    fprintf(stderr, "Expando could not load Python runtime: %s\n", dlerror());
    return 1;
  }

  py_bytes_main_fn py_bytes_main = (py_bytes_main_fn)dlsym(python, "Py_BytesMain");
  if (py_bytes_main == NULL) {
    fprintf(stderr, "Expando could not start Python: %s\n", dlerror());
    return 1;
  }

  int passthrough_count = argc > 1 ? argc - 1 : 1;
  int python_argc = passthrough_count + 3;
  char **python_argv = calloc((size_t)python_argc + 1, sizeof(char *));
  if (python_argv == NULL) {
    fprintf(stderr, "Expando could not allocate launcher arguments.\n");
    return 1;
  }

  python_argv[0] = executable_path;
  python_argv[1] = "-m";
  python_argv[2] = "expando";
  if (argc > 1) {
    for (int index = 1; index < argc; index += 1) {
      python_argv[index + 2] = argv[index];
    }
  } else {
    python_argv[3] = "run";
  }

  return py_bytes_main(python_argc, python_argv);
}
