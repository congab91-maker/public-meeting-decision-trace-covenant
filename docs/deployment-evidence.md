# Studionet Deployment Evidence

- Network: Studionet, Chain ID 61999
- RPC: `https://studio.genlayer.com/api`
- Contract: `0x941CAD8c63C99D5f397018EEe00AabaEcad2E2E1`
- Deploy transaction: `0x68c4a4b60cdc119bd7003659757c606ffb0f85ee950442dff4501b6eb11073c0`
- Deploy receipt: `FINALIZED`, `SUCCESS`, five validators agree
- Deployer: `0xf5C66e5155a62E27047aD4ccE729593D6B9c03Fc`

## E2E consensus success

- Case creation: `0xb7c73e56c8a6d241bf536e8cf6e9605fce65dfc2891443f9d89edebdc5ae2056`
- Agenda artifact: `0x59dfc6f8d26337c2ed430fe1391d70e49b0c56248fca73c0000ed4d0d82fb9d1`
- Announcement artifact: `0x7a736623f48ddf61e49b5748213cf78e89933434248738ec294777fc24619043`
- Seal: `0x1134263d02d22590c9a4d9d782f92b6b9204652ca8476d54dafda2fb5f752fd9`
- Assessment: `0xc57e0c3dbb5d7bfb79bbe2f9d409cd9833d2282d0eb8c20cd259e252049f9985`
- Assessment receipt: `FINALIZED`, `MAJORITY_AGREE`; result `UNRESOLVED`, masks `0/0`, vote `UNKNOWN`
- Authoritative readback: `read_trace("meeting-r6")` returned `['UNRESOLVED', 0, 0, 'UNKNOWN', 1]`
- Sealed manifest readback: `27668a9dfb90dca394b187693bd1483bc92cedd9a7644a156be8fa898a0a934f`

## Negative authorization scenario

- Unauthorized attempt: `0x3f75b3675d0dfd6a444dc2b079963c6978f8bd94c98c4af1a4f645ab7f4b77ec`
- Receipt: `FINALIZED`, `MAJORITY_AGREE`; leader rollback payload `UNAUTHORIZED`
- Post-failure readback remained `['UNRESOLVED', 0, 0, 'UNKNOWN', 1]`
