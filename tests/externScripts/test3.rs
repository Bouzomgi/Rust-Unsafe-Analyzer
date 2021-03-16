// Unsafe usage of external script call with language tag

fn main() {

	#[link(name = "spawnerror", kind = "static")]
	extern "C" {
		fn genSegFault();
	}

}