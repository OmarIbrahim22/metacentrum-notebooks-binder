# MetaCentrum notebooks: Binder launcher

A stable snapshot of the
[metacentrum-notebooks](https://github.com/OmarIbrahim22/metacentrum-notebooks)
project, packaged so that [e-INFRA CZ BinderHub](https://binderhub.cloud.e-infra.cz/)
can open it as a ready-to-run Jupyter session. You need an e-INFRA CZ /
MetaCentrum login; nothing has to be installed.

[![Launch on e-INFRA BinderHub](https://binderhub.cloud.e-infra.cz/badge_logo.svg)](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/00_environment_check.ipynb)

The first launch after an update builds the environment and takes several
minutes. Later launches start from the finished image.

## Open a specific notebook

| # | Notebook | In a Binder session |
|---|----------|---------------------|
| 00 | [Environment Check](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/00_environment_check.ipynb) | Runs fully |
| 01 | [S3 Object Storage](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/01_s3_object_storage.ipynb) | Needs your own S3 credentials |
| 02 | [Invenio Repository](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/02_invenio_repository.ipynb) | Needs your own NRP token |
| 03 | [OpenStack API](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/03_openstack_api.ipynb) | Needs your own OpenStack application credentials |
| 04 | [Open WebUI Chat API](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/04_open_webui_chat_api.ipynb) | Needs your own AI API token |
| 05 | [GPU Container + AI Model](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/gpu?labpath=notebooks/05_gpu_container_ai_model.ipynb) | Opens with a GPU requested; the container steps cannot run inside Binder |
| 06 | [R Kernel Demo](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/06_r_kernel_demo.ipynb) | Runs on the R kernel |
| 07 | [MATLAB Kernel Demo](https://binderhub.cloud.e-infra.cz/v2/gh/OmarIbrahim22/metacentrum-notebooks-binder/main?labpath=notebooks/07_matlab_kernel_demo.ipynb) | Read only; Binder has no MATLAB |

For credentials, run the setup cell in notebook 00 or see `env.example`.
Credentials you enter stay in your own session and are never written to this
repository.

## What is in this repo

```
notebooks/        snapshot of the notebooks (.ipynb only)
src/mcnb/         helper package the notebooks import
pyproject.toml    its dependency list
env.example       credential template used by the setup wizard
SOURCE_COMMIT     which thesis-repo commit the snapshot was taken from
binder/           environment BinderHub builds: Python 3.11, R kernel, pip install -e ".[all]"
sync.py           refreshes the snapshot
```

`notebooks/`, `src/`, `pyproject.toml` and `env.example` are copies. Do not
edit them here; change the thesis repo and take a new snapshot.

## Branches

- `main`: no GPU. Use this for everything except notebook 05.
- `gpu`: identical, plus a `.resources` file with `gpu=1`, which asks e-INFRA
  BinderHub for one GPU per session. Linked only from notebook 05 so that
  ordinary launches do not reserve a card.

## Updating the snapshot

Reviewers see only what is committed here, so the published version changes
only when you run this:

```bash
python sync.py                     # copy the thesis repo's committed HEAD
git add -A && git commit -m "Snapshot $(head -c 7 SOURCE_COMMIT)"
git checkout gpu && git merge main && git checkout main
git push origin main gpu
```

`sync.py` copies committed files only and refuses to run while the thesis repo
has uncommitted changes (`--allow-dirty` overrides that). BinderHub rebuilds
the environment on the next launch.

For a link that keeps pointing at one exact version even after later
snapshots, tag this repo (`git tag v1 && git push origin v1`) and replace
`main` in the link with the tag.
