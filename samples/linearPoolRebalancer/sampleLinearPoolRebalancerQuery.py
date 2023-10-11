import json

import balpy


def main():
    network = "mainnet"

    linear_pool_addresses = [
        "0x0a0fb4ff697de5ac5b6770cd8ee1b72af80b57cf",
        "0x8e6ec57a822c2f527f2df7c7d7d361df3e7530a1",
        "0x9b1c8407a360443a9e5eca004713e4088fab8ac0",
        "0xac5b4ef7ede2f2843a704e96dcaa637f4ba3dc3f",
        "0xd6e355036f41dc261b3f1ed3bbc6003e87aadb4f",
        "0x0afbd58beca09545e4fb67772faf3858e610bcd0",
        "0x126e7643235ec0ab9c103c507642dc3f4ca23c66",
        "0x159cb00338fb63f263fd6f621df619cef71da954",
        "0x246ffb4d928e394a02e45761fecdba6c2e79b8eb",
        "0x2b218683178d029bab6c9789b1073aa6c96e5176",
        "0x2ff1a9dbdacd55297452cfd8a4d94724bc22a5f7",
        "0x335d1709d4da9aca59d16328db5cd4ea66bfe06b",
        "0x3fcb7085b8f2f473f80bf6d879cae99ea4de9344",
        "0x60d604890feaa0b5460b28a424407c24fe89374a",
        "0x6667c6fa9f2b3fc1cc8d85320b62703d938e4385",
        "0x7337224d59cb16c2dc6938cd45a7b2c60c865d6a",
        "0x8f4063446f5011bc1c9f79a819efe87776f23704",
        "0x9516a2d25958edb8da246a320f2c7d94a0dbe25d",
        "0xa1697f9af0875b63ddc472d6eebada8c1fab8568",
        "0xb0f75e97a114a4eb4a425edc48990e6760726709",
        "0xbb6881874825e60e1160416d6c426eae65f2459e",
        "0xbc0f2372008005471874e426e86ccfae7b4de79d",
        "0xc50d4347209f285247bda8a09fc1c12ce42031c3",
        "0xc8c79fcd0e859e7ec81118e91ce8e4379a481ee6",
        "0xcbfa4532d8b2ade2c261d3dd5ef2a2284f792692",
        "0xcfae6e251369467f465f13836ac8135bd42f8a56",
        "0xdba274b4d04097b90a72b62467d828cefd708037",
        "0xf22ff21e17157340575158ad7394e068048dd98b",
        "0xfa24a90a3f2bbe5feea92b95cd0d14ce709649f9",
        "0xfef969638c52899f91781f1be594af6f40b99bad",
        "0x0d05aac44ac7dd3c7ba5d50be93eb884a057d234",
        "0x4a82b580365cff9b146281ab72500957a849abdc",
        "0xa8b103a10a94f4f2d7ed2fdcd5545e8075573307",
        "0xe03af00fabe8401560c1ff7d242d622a5b601573",
        "0x2bbf681cc4eb09218bee85ea2a5d3d13fa40fc0c",
        "0x2f4eb100552ef93840d5adc30560e5513dfffacb",
        "0x331d50e0b00fc1c32742f151e56b9b616227e23e",
        "0x3bb22fc9033b802f2ac47c18885f63476f158afc",
        "0x3cdae4f12a67ba563499e102f309c73213cb241c",
        "0x454ed96955d04d2f5cdd05e0fd1c77975bfe5307",
        "0x4ce277df0feb5b4d07a0ca2adcf5326e4005239d",
        "0x652d486b80c461c397b0d95612a404da936f3db3",
        "0x6a1eb2e9b45e772f55bd9a34659a04b6f75da687",
        "0x804cdb9116a10bb78768d3252355a1b18067bf8f",
        "0x813e3fe1761f714c502d1d2d3a7cceb33f37f59d",
        "0x82698aecc9e28e9bb27608bd52cf57f704bd1b83",
        "0x9210f1204b5a24742eba12f710636d76240df3d0",
        "0xa3823e50f20982656557a4a6a9c06ba5467ae908",
        "0xae37d54ae477268b9997d4161b96b8200755935c",
        "0xbfa413a2ff0f20456d57b643746133f54bfe0cd2",
        "0xdc063deafce952160ec112fa382ac206305657e6",
        "0xe6bcc79f328eec93d4ec8f7ed35534d9ab549faa",
        "0xfd11ccdbdb7ab91cb9427a6d6bf570c95876d195",
        "0x395d8a1d9ad82b5abe558f8abbfe183b27138af4",
        "0x74cbfaf94a3577c539a9dcee9870a6349a33b34f",
    ]

    bal = balpy.balpy.balpy(network)
    output = bal.balGetRebalanceLinearPoolsData(linear_pool_addresses)

    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()
